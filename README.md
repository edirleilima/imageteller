# ImageTeller - An AI-powered Storyteller

ImageTeller is an AI-powered system that composes stories from images. Given a single image or an ordered sequence of images, it interprets their visual content with a multimodal model and weaves the scenes into a coherent, chapter-structured narrative, illustrating each chapter with a generated image. 

To compose a story, the user uploads and arranges the images, optionally attaches a caption to each one to steer how it is interpreted, and selects a genre. ImageTeller then generates the story chapter by chapter and presents it as an illustrated book. The user stays in the loop throughout: regenerating an individual chapter, regenerating a chapter's illustration, or rejecting and restarting the whole story from the same input. Saved stories are collected in the user's personal library.

Narratives can follow one of five fundamental genres (Comedy, Romance, Tragedy, Satire, or Mystery), or a data storytelling mode that turns the images into an insight-driven narrative. Stories can also be guided by player-driven types based on Bartle's taxonomy (Achiever, Explorer, Socializer, and Killer), or the system can be left free to decide how to structure the plot. Internally, the work is divided among specialized AI agents: a Visual Analyzer, a Storywriter, a Plot Manager, and an Illustrator.

## Publications

ImageTeller and the image-driven narrative-generation approach behind it are described in the following publications:

1. Edirlei Soares de Lima, Margot M. E. Neggers, Marco A. Casanova, Antonio L. Furtado. From Images to Stories: Exploring Player-Driven Narratives in Games. *14th International Conference on Videogame Sciences and Arts (VIDEOJOGOS 2024)*, Leiria, Portugal, 2024. https://doi.org/10.1007/978-3-031-81713-7_16
2. Edirlei Soares de Lima, Marco A. Casanova, Antonio L. Furtado. Imagining from Images with an AI Storytelling Tool. *arXiv:2408.11517 [cs.CL]*, August 2024. https://doi.org/10.48550/arXiv.2408.11517

## Components

The repository is split into three folders:

- `web/` - the user-facing React interface, built with Vite.
- `api/` - a FastAPI service that handles generation (image analysis, text, and illustrations) and persistence.
- `db/` - the MySQL schema.

The web interface calls the API over HTTP under the `/imageteller-api/` path, so a typical deployment serves both from the same domain and the web server reverse-proxies that path to the API container.

## Requirements

- MySQL 8.0+ or MariaDB
- Docker, to run the API
- A web server (Apache or Nginx) to serve the built static files and reverse-proxy the API
- A reachable ComfyUI instance and at least one LLM provider (OpenAI, Ollama, or vLLM); image analysis can use OpenAI or a separate Ollama vision endpoint
- A running instance of the [NLP API](https://github.com/edirleilima/nlp-api), reachable from the API container

## Deployment

### 1. Database

Create the schema on your MySQL/MariaDB server:

```bash
mysql -u youruser -p < imageteller-db/schema.sql
```

### 2. API

Fill in an environment file from `imageteller-api/.env.example` (every variable is documented there). Then build the image and run the container:

```bash
docker build -t imageteller-api ./imageteller-api

docker run -d --name imageteller-api \
  --env-file /path/to/imageteller.env \
  -p 8001:8001 \
  -v /path/to/data/images:/imageteller/images \
  -v /path/to/data/chapters:/imageteller/chapters \
  --restart unless-stopped \
  imageteller-api
```

The mounted volumes hold the uploaded source images (`images/`) and the generated chapter illustrations (`chapters/`), so set `DATA_PATH=/imageteller` in the environment file to match them.

### 3. Web interface

Copy `imageteller-web/.env.example` to `imageteller-web/.env` and fill it in (`VITE_API_BASE_URL` and `VITE_PLACEHOLDER_IMAGE_URL`). Then build:

```bash
cd imageteller-web
npm install
npm run build
```

Vite outputs the production bundle to `imageteller-web/build/`. Deploy its contents to your web server under the `/imageteller` path (set via `base` in `vite.config.js`), and configure the server to forward requests under `/imageteller-api/` to the API container's host port (`8001` in the example above). For local development, `npm run dev` serves the app on port 3000.

## License

Released under the MIT License.
