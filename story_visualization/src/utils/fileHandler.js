// Helper to organize files into categories
export function organizeFiles(fileList) {
  const texts = [];
  const v1Jsons = {};
  const v2Jsons = {};
  const v3Jsons = {};

  Array.from(fileList).forEach((file) => {
    const path = file.webkitRelativePath || file.name;
    const pathLower = path.toLowerCase();
    const parts = path.split('/');
    const fileName = parts.pop();
    const dir = parts.join('/');

    // Process .txt files from texts folder
    if (fileName.endsWith('.txt') && 
        (pathLower.includes('/texts/') || pathLower.startsWith('texts/'))) {
      const id = fileName.replace('.txt', '');
      texts.push({ file, id, path, name: fileName });
    }
    // Process .json files from json/json_v2/json_v3 folders (for annotation loading)
    else if (fileName.endsWith('.json')) {
      // Skip JSON files in texts folder
      if (pathLower.includes('/texts/') || pathLower.startsWith('texts/')) {
        return;
      }
      
      const id = fileName.replace(/_v[123]\.json$/, '').replace('.json', '');
      
      // Determine version from folder or filename
      const isV2Folder = dir.endsWith('json_v2') || dir.includes('/json_v2/');
      const isV2File = fileName.endsWith('_v2.json');
      const isV3Folder = dir.endsWith('json_v3') || dir.includes('/json_v3/');
      const isV3File = fileName.endsWith('_v3.json');
      
      if (isV3Folder || isV3File) {
        v3Jsons[id] = file;
      } else if (isV2Folder || isV2File) {
        v2Jsons[id] = file;
      } else {
        v1Jsons[id] = file;
      }
    }
  });

  return { texts, v1Jsons, v2Jsons, v3Jsons };
}
