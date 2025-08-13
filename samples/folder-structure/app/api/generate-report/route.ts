// app/api/generate-report/route.ts
import { OpenAI } from "openai";
import { FoundryLocalManager } from "foundry-local-sdk";
import { NextRequest } from "next/server";

const alias = "Phi-3.5-mini-instruct-generic-cpu";

let foundryLocalManager: FoundryLocalManager | undefined;
let modelInfo: any;
let openai: OpenAI | undefined;

async function ensureModelInitialized() {
  if (!foundryLocalManager || !modelInfo || !openai) {
    foundryLocalManager = new FoundryLocalManager();
    modelInfo = await foundryLocalManager.init(alias);
    if (!modelInfo) throw new Error("Model not found");
    openai = new OpenAI({
      baseURL: foundryLocalManager.endpoint,
      apiKey: foundryLocalManager.apiKey,
    });
  }
}
export async function POST(request: NextRequest) {
  try {
    await ensureModelInitialized();

    const { files } = await request.json();
    const fileListString = JSON.stringify(files, null, 2);

    const prompt = `Generate a full and detailed report based on the following file list:\n\n${fileListString}\n\nPlease provide a comprehensive analysis, including file types, sizes, and any other relevant information. The report should be structured and easy to read, with sections for each file type and folder. Use bullet points or tables where appropriate to enhance clarity.`;

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

    // Create a ReadableStream
    const readableStream = new ReadableStream({
      async start(controller) {
        try {
          for await (const chunk of stream) {
            const content = chunk.choices[0]?.delta?.content;
            if (content) {
              // Send each chunk as a text encoder
              controller.enqueue(new TextEncoder().encode(content));
            }
          }
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