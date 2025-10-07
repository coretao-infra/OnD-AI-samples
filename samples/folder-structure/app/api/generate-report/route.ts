// app/api/generate-report/route.ts
import { OpenAI } from "openai";
import { FoundryLocalManager } from "foundry-local-sdk";
import { NextRequest } from "next/server";

const alias = "phi-3.5-mini";
const max_filelist_size = 1000; // maximum number of characters in the list output to process

let foundryLocalManager: FoundryLocalManager | undefined;
let modelInfo: any;
let openai: OpenAI | undefined;

async function ensureModelInitialized() {
  if (!foundryLocalManager || !modelInfo || !openai) {
    // 1) Create the Foundry Local manager and start the service
    foundryLocalManager = new FoundryLocalManager();
    await foundryLocalManager.init(alias);

    // 2) Fetch model metadata (throws if not found)
    modelInfo = await foundryLocalManager.getModelInfo(alias, /*throwOnNotFound*/ true);

    // 3) Ensure the model is loaded: download if necessary, then load into inference server
    const loaded = await foundryLocalManager.listLoadedModels();
    if (!loaded.some(m => m.id === modelInfo.id)) {
      await foundryLocalManager.downloadModel(alias);
      await foundryLocalManager.loadModel(alias);
    }

    // 4) Initialize OpenAI client with the local endpoint and API key
    openai = new OpenAI({
      baseURL: foundryLocalManager.endpoint,
      apiKey: foundryLocalManager.apiKey,
    });
  }
}

// Helper: flatten nested file structure into a list of relative paths
function flattenFileTree(nodes: any[], parentPath = ""): string[] {
  return nodes.flatMap(node => {
    const path = parentPath ? `${parentPath}/${node.name}` : node.name;
    if (node.isFolder && Array.isArray(node.children)) {
      // Append slash for folders
      return [path + "/", ...flattenFileTree(node.children, path)];
    }
    return [path];
  });
}

export async function POST(request: NextRequest) {
  try {
    await ensureModelInitialized();

    const { files } = await request.json();
    // Flatten and list file/folder paths
    const flattened = flattenFileTree(files as any[]);
    let rawList = flattened.join("\n");
    // Truncate if exceeds maximum allowed length, and record a notice
    let truncatedNotice = "";
    if (rawList.length > max_filelist_size) {
      console.warn(`DEBUG: fileList length ${rawList.length} > max ${max_filelist_size}, truncating.`);
      rawList = rawList.slice(0, max_filelist_size);
      truncatedNotice = `NOTE: File list truncated to first ${max_filelist_size} characters.\n\n`;
    }
    const fileListString = rawList;

    const prompt = `Generate a full and detailed report based on the following file list:\n\n${truncatedNotice}${fileListString}\n\nMore than only merely restating what would be evident from the folder/file list, lease enrich with a comprehensive assessment. When and where relevant, include file types, sizes, and any other contextually-useful information. The report should be structured and easy to read, with sections for each file type and folder. Use bullet points or tables where appropriate to enhance clarity.`;

    // Debug: log prompt and its size in bytes
    console.log('DEBUG: prompt =', prompt);
    const promptBytes = new TextEncoder().encode(prompt).length;
    console.log(`DEBUG: prompt size = ${promptBytes} bytes`);

    // Call the Foundry Local model inference
    const stream = await openai!.chat.completions.create({
      model: modelInfo.id,
      messages: [
        {
          role: "user",
          content: prompt,
        },
      ],
      max_tokens: 1000,
      temperature: 0.7,
      stream: true,
    });

    // Debug: log stream object and its serialized size
    console.log('DEBUG: stream =', stream);
    try {
      const serialized = JSON.stringify(stream);
      const streamBytes = new TextEncoder().encode(serialized).length;
      console.log(`DEBUG: stream serialized size = ${streamBytes} bytes`);
    } catch {
      console.log('DEBUG: stream not JSON-serializable');
    }

    // Create a ReadableStream with metadata summary and performance stats
    const readableStream = new ReadableStream({
      async start(controller) {
        // Emit combined summary with placeholders for streaming stats
        const summaryHeader = `Summary:
` +
          `- Prompt size: ${promptBytes} bytes
` +
          `- Model alias: ${alias}
` +
          `- Model ID: ${modelInfo.id}
` +
          `- Response size: pending...
` +
          `- Approx tokens: pending...
` +
          `- Throughput: pending...

`;
        controller.enqueue(new TextEncoder().encode(summaryHeader));
        // Track response size and timing
        const startTime = Date.now();
        let responseBytes = 0;
        try {
          for await (const chunk of stream) {
            const content = chunk.choices[0]?.delta?.content;
            if (content) {
              const chunkBytes = new TextEncoder().encode(content).length;
              responseBytes += chunkBytes;
              controller.enqueue(new TextEncoder().encode(content));
            }
          }
          // After streaming, compute stats and emit updated summary
          const duration = (Date.now() - startTime) / 1000; // seconds
          const approxTokens = Math.round(responseBytes / 4);
          const rate = (approxTokens / duration).toFixed(1);
          const summaryUpdate = `

Summary Update:
` +
            `- Response size: ${responseBytes} bytes
` +
            `- Approx tokens: ${approxTokens}
` +
            `- Throughput: ${rate} tokens/sec
`;
          controller.enqueue(new TextEncoder().encode(summaryUpdate));
          controller.close();
        } catch (error) {
          controller.error(error);
        }
      },
    });

    return new Response(readableStream, {
      headers: {
        'Content-Type': 'text/plain',
        'Transfer-Encoding': 'chunked',
      },
    });
  } catch (error) {
    console.error("Error in streaming:", error);
    return Response.json({ error: "Failed to generate report" }, { status: 500 });
  }
}