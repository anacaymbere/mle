import axios from 'axios';
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

const IMAGE_DIR = path.resolve(__dirname, 'cat-images');
const IMAGE_COUNT = 200;

// Função para buscar URLs de imagens de gatos via API do DuckDuckGo (alternativa ao Google Images, pois Google não disponibiliza API pública gratuita)
async function fetchCatImageUrls(count: number): Promise<string[]> {
  const urls: string[] = [];
  let offset = 0;

  while (urls.length < count) {
    const response = await axios.get('https://duckduckgo.com/i.js', {
      params: {
        q: 'cats',
        s: offset,
        o: 'json',
        p: 1,
      },
      headers: {
        'User-Agent': 'Mozilla/5.0',
      },
    });

    const results = response.data.results as Array<{ image: string }>;
    for (const result of results) {
      if (urls.length >= count) break;
      urls.push(result.image);
    }

    if (!response.data.next) break;
    offset += results.length;
  }

  return urls.slice(0, count);
}

// Função para baixar uma imagem a partir da URL
async function downloadImage(url: string, filepath: string): Promise<void> {
  const response = await axios.get(url, { responseType: 'stream' });
  await new Promise<void>((resolve, reject) => {
    const stream = response.data.pipe(fs.createWriteStream(filepath));
    stream.on('finish', () => resolve());
    stream.on('error', reject);
  });
}

// Inicializa repositório git e realiza commit + push
function pushToGitHub(directory: string, commitMessage: string) {
  try {
    execSync('git init', { cwd: directory });
    execSync('git add .', { cwd: directory });
    execSync(`git commit -m "${commitMessage}"`, { cwd: directory });
    execSync('git branch -M main', { cwd: directory });
    // Configurar seu repositório remoto abaixo:
    // Substitua URL abaixo pela URL do seu repositório GitHub
    const remoteUrl = 'git@github.com:seu-usuario/seu-repositorio.git';
    execSync(`git remote add origin ${remoteUrl}`, { cwd: directory });
    execSync('git push -u origin main', { cwd: directory });
    console.log('Imagens enviadas para o GitHub com sucesso.');
  } catch (error) {
    console.error('Erro ao enviar para o GitHub:', error);
  }
}

// Função principal
async function main() {
  if (!fs.existsSync(IMAGE_DIR)) {
    fs.mkdirSync(IMAGE_DIR);
  }

  console.log(`Buscando URLs de ${IMAGE_COUNT} imagens de gatos...`);
  const urls = await fetchCatImageUrls(IMAGE_COUNT);

  console.log(`Baixando imagens para o diretório ${IMAGE_DIR}...`);
  for (let i = 0; i < urls.length; i++) {
    const ext = path.extname(urls[i]).split('?')[0] || '.jpg';
    const filename = `cat-${i + 1}${ext}`;
    const filepath = path.join(IMAGE_DIR, filename);
    try {
      await downloadImage(urls[i], filepath);
      process.stdout.write(`Baixada imagem ${i + 1} de ${urls.length}\r`);
    } catch {
      console.warn(`Falha ao baixar imagem: ${urls[i]}`);
    }
  }
  console.log('\nDownload concluído.');

  // Commit e push para GitHub
  pushToGitHub(IMAGE_DIR, `Adiciona ${urls.length} imagens de gatos`);
}

main().catch(console.error);
