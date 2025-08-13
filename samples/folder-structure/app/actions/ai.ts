"use server";
import { OpenAI } from "openai";
import { FoundryLocalManager } from "foundry-local-sdk";
import { FileEntry } from "../page";

const alias = "Phi-3.5-mini-instruct-generic-gpu";

const foundryLocalManager = new FoundryLocalManager();
const modelInfo = await foundryLocalManager.init(alias);
if (!modelInfo) throw new Error("Model not found");

const openai = new OpenAI({
  baseURL: foundryLocalManager.endpoint,
  apiKey: foundryLocalManager.apiKey,
});

export async function* generateTextStream(listFiles: FileEntry[]) {
  if (!modelInfo) {
    throw new Error("Model info is not initialized");
  }

  const fileListString = JSON.stringify(listFiles, null, 2);
  console.log("File list string:", fileListString);

  const prompt = `Generate a full and detailed report based on the following file list:\n\n${fileListString}\n\nPlease provide a comprehensive analysis, including file types, sizes, and any other relevant information. The report should be structured and easy to read, with sections for each file type and folder. Use bullet points or tables where appropriate to enhance clarity.`;
  console.log("Prompt:", prompt);

  try {
    const stream = await openai.chat.completions.create({
      model: modelInfo.id,
      messages: [
        {
          role: "user",
          content: prompt,
        },
      ],
      max_tokens: 1000,
      temperature: 0.7,
      stream: true, // Enable streaming
    });

    for await (const chunk of stream) {
      const content = chunk.choices[0]?.delta?.content;
      if (content) {
        yield content;
      }
    }
  } catch (error) {
    console.error("Error in streaming:", error);
    throw error;
  }
}