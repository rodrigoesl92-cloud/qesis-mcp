import fs from 'fs';
import path from 'path';

const FSQCA_DIR = path.join(process.cwd(), 'data/fsqca');
const NOTION_DIR = path.join(process.cwd(), 'content/notion-archives');

export function getFsQCAMatrix(fileName: string) {
  try {
    const filePath = path.join(FSQCA_DIR, `${fileName}.csv`);
    const fileContents = fs.readFileSync(filePath, 'utf8');
    
    const rows = fileContents.split('\n').filter(row => row.trim() !== '');
    const headers = rows[0].split(',');
    const data = rows.slice(1).map(row => {
      const values = row.split(',');
      return headers.reduce((obj, header, index) => {
        obj[header.trim()] = values[index]?.trim();
        return obj;
      }, {} as Record<string, string>);
    });

    return { success: true, data };
  } catch (error: any) {
    console.error(`Failed to load fsQCA matrix: ${fileName}`, error);
    return { success: false, error: error.message };
  }
}

export function getArchivedNotionContent(fileName: string) {
  try {
    const filePath = path.join(NOTION_DIR, `${fileName}.md`);
    const content = fs.readFileSync(filePath, 'utf8');
    return { success: true, content };
  } catch (error: any) {
    console.error(`Failed to load Notion archive: ${fileName}`, error);
    return { success: false, error: error.message };
  }
}
