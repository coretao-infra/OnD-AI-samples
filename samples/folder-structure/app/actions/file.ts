"use server";

import * as fs from 'fs';
import * as path from 'path';

interface FileEntry {
  name: string;
  extension: string | null; // null if folder
  isFolder: boolean;
  children?: FileEntry[];  // only for folders
}

/**
 * Recursively list files and folders at `dirPath`
 * @param dirPath Absolute or relative path to directory
 * @returns FileEntry[] representing folder contents hierarchically
 */
export async function listFilesRecursive(dirPath: string): Promise<FileEntry[]> {
  const entries: FileEntry[] = [];

  // Read directory contents
  const items = fs.readdirSync(dirPath, { withFileTypes: true });

  for (const item of items) {
    const fullPath = path.join(dirPath, item.name);

    if (item.isDirectory()) {
      // It's a folder, recurse
      entries.push({
        name: item.name,
        extension: null,
        isFolder: true,
        children: await listFilesRecursive(fullPath),
      });
    } else if (item.isFile()) {
      // It's a file
      entries.push({
        name: item.name,
        extension: path.extname(item.name).slice(1), // remove dot
        isFolder: false,
      });
    }
    // Could handle symlinks or other types if needed
  }

  return entries;
}

// Example usage: generate JSON and save to file
if (require.main === module) {
  (async () => {
    const targetPath = process.argv[2] || '.'; // take path from command line or default to current dir
    const result = await listFilesRecursive(targetPath);
    const outputPath = 'fileList.json';

    fs.writeFileSync(outputPath, JSON.stringify(result, null, 2), 'utf-8');
    console.log(`File list saved to ${outputPath}`);
  })();
}
