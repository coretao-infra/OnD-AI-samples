"use client";

import { useState, useTransition } from "react";
import { listFilesRecursive } from "@/app/actions/file";
import { generateTextStream } from "@/app/actions/ai"; // Adjust import path as needed
import Spinner from "@/components/Spinner";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github.css";

export interface FileEntry {
  name: string;
  extension: string | null; // null if folder
  isFolder: boolean;
}

export default function FileExplorerPage() {
  const [path, setPath] = useState("");
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedReport, setGeneratedReport] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!path.trim()) return;

    startTransition(async () => {
      try {
        setError(null);
        const result = await listFilesRecursive(path);
        console.log(result); // For debugging
        setFiles(result); // Replace 'path' with the correct property if needed
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
        setFiles([]);
      }
    });
  };

  const generateReport = async () => {
    setIsGenerating(true);
    setGeneratedReport("");
    setError(null);

    try {
      const response = await fetch("/api/generate-report", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ files }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error("Response body is not readable");
      }

      setIsGenerating(false);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          setGeneratedReport((prev) => prev + chunk); // Append to previous content
        }
      } finally {
        reader.releaseLock();
      }
    } catch (err) {
      console.error("Error generating text:", err);
      setError(err instanceof Error ? err.message : "Failed to generate text");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">File Explorer</h1>

        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="path"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Directory Path
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  id="path"
                  value={path}
                  onChange={(e) => setPath(e.target.value)}
                  placeholder="Enter directory path (e.g., /home/user/documents)"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-black"
                  disabled={isPending}
                />
                <button
                  type="submit"
                  disabled={isPending || !path.trim()}
                  className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isPending ? "Loading..." : "List Files"}
                </button>
              </div>
            </div>
          </form>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-8">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-red-400"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Error occurred
                </h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
              </div>
            </div>
          </div>
        )}

        {files.length > 0 && (
          <div className="bg-white rounded-lg shadow-md">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">
                Files Found ({files.length})
              </h2>
              <p className="text-sm text-gray-600 mt-1">Directory: {path}</p>
            </div>
            <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
              {files.map((file, index) => (
                <div key={index} className="px-6 py-3 hover:bg-gray-50">
                  <div className="flex items-center">
                    <svg
                      className="h-4 w-4 text-gray-400 mr-2 flex-shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    <span className="text-sm text-gray-900 font-mono break-all">
                      {file.name}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <div></div>
            <div
              onClick={generateReport}
              className="cursor-pointer mt-5 bg-blue-600 px-5 py-5 text-white rounded-md text-center"
            >
              Generate AI Response
            </div>
            {isGenerating && (
              <div className="mt-4 text-sm text-gray-500 w-full h-96 flex flex-col items-center justify-center">
                <div>
                  <Spinner />
                </div>
                <div>Generating report, please wait...</div>
              </div>
            )}
            {generatedReport && (
              <div className="mt-4 p-4 bg-gray-100 rounded-md">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Generated Report:
                </h3>
                <div className="p-6">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeHighlight]}
                    components={{
                      // Custom styling for different elements
                      h1: ({ node, ...props }) => (
                        <h1
                          className="text-2xl font-bold mb-4 text-gray-800 border-b border-gray-200 pb-2"
                          {...props}
                        />
                      ),
                      h2: ({ node, ...props }) => (
                        <h2
                          className="text-xl font-semibold mb-3 text-gray-800 mt-6"
                          {...props}
                        />
                      ),
                      h3: ({ node, ...props }) => (
                        <h3
                          className="text-lg font-medium mb-2 text-gray-800 mt-4"
                          {...props}
                        />
                      ),
                      p: ({ node, ...props }) => (
                        <p
                          className="mb-4 text-gray-700 leading-relaxed"
                          {...props}
                        />
                      ),
                      ul: ({ node, ...props }) => (
                        <ul
                          className="list-disc list-inside mb-4 text-gray-700 space-y-1"
                          {...props}
                        />
                      ),
                      ol: ({ node, ...props }) => (
                        <ol
                          className="list-decimal list-inside mb-4 text-gray-700 space-y-1"
                          {...props}
                        />
                      ),
                      li: ({ node, ...props }) => (
                        <li className="ml-4" {...props} />
                      ),
                      code: ({ node, ...props }) => (
                        <code
                          className="block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto"
                          {...props}
                        />
                      ),
                      pre: ({ node, ...props }) => (
                        <pre className="mb-4 overflow-x-auto" {...props} />
                      ),
                      blockquote: ({ node, ...props }) => (
                        <blockquote
                          className="border-l-4 border-blue-500 pl-4 py-2 mb-4 bg-blue-50 text-gray-700 italic"
                          {...props}
                        />
                      ),
                      table: ({ node, ...props }) => (
                        <table
                          className="min-w-full border-collapse border border-gray-300 mb-4 text-black"
                          {...props}
                        />
                      ),
                      th: ({ node, ...props }) => (
                        <th
                          className="border border-gray-300 px-4 py-2 bg-gray-100 font-semibold text-left"
                          {...props}
                        />
                      ),
                      td: ({ node, ...props }) => (
                        <td
                          className="border border-gray-300 px-4 py-2"
                          {...props}
                        />
                      ),
                      strong: ({ node, ...props }) => (
                        <strong
                          className="font-semibold text-gray-900"
                          {...props}
                        />
                      ),
                      em: ({ node, ...props }) => (
                        <em className="italic text-gray-700" {...props} />
                      ),
                    }}
                  >
                    {generatedReport}
                  </ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        )}

        {!isPending && files.length === 0 && !error && path && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-yellow-400"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  No files found
                </h3>
                <div className="mt-2 text-sm text-yellow-700">
                  The directory appears to be empty or the path may not exist.
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
