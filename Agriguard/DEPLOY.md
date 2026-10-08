# AgriGuard - Deployment Guide (Render Free Tier)

This guide walks through deploying **AgriGuard** as a single, highly-optimized Docker container on [Render's Free Web Service](https://render.com) (512 MB RAM limit).

---

## 🏗 Architecture & Memory Optimizations

To comfortably fit inside Render's **512 MB RAM** limit with zero crashes ($< 400\text{ MB}$ runtime footprint):
1. **No PyTorch at Runtime**: The deep-learning MobileNetV2 model is exported to **ONNX** (`ml/outputs/agriguard_model.onnx`, 8.64 MB) and executed via `onnxruntime` CPU with pure NumPy/Pillow image preprocessing.
2. **Unified Single Container**: The React frontend is pre-built and served directly by FastAPI via SPA static file routing, eliminating the need for a separate Node.js server.
3. **Headless OpenCV & Lazy Imports**: Uses `opencv-python-headless` and lazily initialized vectorizers.
4. **Image Auto-Downscaling**: Uploaded images are resized to a maximum dimension of 1024 px before running OpenCV HSV segmentation and ONNX inference.
5. **Single Worker**: Uvicorn runs with 1 worker (`--workers 1`).
6. **Automatic Demo Seeding**: Since Render Free tier disk is ephemeral, setting `SEED_DEMO=true` provisions sample farmer and expert accounts on every boot.

---

## 🔑 Environment Variables Reference

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `PORT` | `10000` | Port uvicorn binds to (Render sets this dynamically) |
| `JWT_SECRET` | *Auto-generated* | Secret key for signing JWT tokens (**Required in Production**) |
| `DATABASE_URL` | `sqlite:///./data/agriguard.db` | SQLite database URI |
| `MODEL_PATH` | `ml/outputs/agriguard_model.onnx` | Path to the ONNX model |
| `CHATBOT_BACKEND` | `rules` | Retrieval engine: `rules` or `ollama` |
| `UPLOAD_DIR` | `uploads` | Directory for raw images and disease overlay masks |
| `SEED_DEMO` | `true` | Auto-seeds demo accounts and sample reports on startup |
| `ALLOWED_ORIGINS`| `*` | Allowed CORS origins (comma-separated or `*`) |

---

## 🚀 Option 1: Deploying via Render Blueprint (`render.yaml`)

1. **Push your repository to GitHub**:
   ```bash
   git add .
   git commit -m "Deploy AgriGuard to Render"
   git push origin main
   ```

2. **Connect to Render**:
   - Log in to your [Render Dashboard](https://dashboard.render.com).
   - Click **New +** -> **Blueprint**.
   - Connect your GitHub repository containing `render.yaml`.
   - Render will automatically detect the Docker service and generate a secure `JWT_SECRET`.
   - Click **Apply**.

---

## 🛠 Option 2: Deploying via Render Web Service (Manual UI)

1. Go to [Render Dashboard](https://dashboard.render.com) -> **New +** -> **Web Service**.
2. Select **Build and deploy from a Git repository**.
3. Choose your repository and configure:
   - **Name**: `agriguard`
   - **Language / Runtime**: `Docker`
   - **Branch**: `main`
   - **Plan**: `Free` (512 MB RAM, 0.1 CPU)
   - **Health Check Path**: `/health`
4. Add Environment Variables:
   - `JWT_SECRET`: *(Click Generate or enter a 32+ character random string)*
   - `DATABASE_URL`: `sqlite:///./data/agriguard.db`
   - `MODEL_PATH`: `ml/outputs/agriguard_model.onnx`
   - `SEED_DEMO`: `true`
   - `UPLOAD_DIR`: `uploads`
   - `ALLOWED_ORIGINS`: `*`
5. Click **Create Web Service**.

---

## 🧪 Local Docker Verification

To test the production container locally before deploying:

```bash
# 1. Build Docker image
docker build -t agriguard:latest .

# 2. Run container
docker run -p 10000:10000 \
  -e JWT_SECRET="local-docker-test-secret-key-12345" \
  -e SEED_DEMO="true" \
  agriguard:latest

# 3. Test Health Check
curl http://localhost:10000/health
# Output: {"status":"ok"}

# 4. Open in Browser
# Visit http://localhost:10000
```

---

## 👨‍🌾 Default Demo Credentials

When `SEED_DEMO=true` is set, these accounts are ready for testing immediately upon boot:

| Role | Email | Password |
| :--- | :--- | :--- |
| **Farmer** | `ramesh@farmer.in` | `farmer123` |
| **Expert** | `expert@agriguard.in` | `expert123` |

---

## ⏱ Cold Starts on Render Free Tier

- Render spins down free web services after **15 minutes of inactivity**.
- The first incoming HTTP request will wake the container (cold start), which typically takes **30 to 50 seconds**.
- Once warm, requests respond in under **100 ms** and model inference takes $\sim 40\text{ ms}$.

---

## 🩺 Troubleshooting & Out-Of-Memory (OOM)

If you see memory warnings or container restarts in Render logs:
1. **Verify ONNX is used**: Ensure `MODEL_PATH=ml/outputs/agriguard_model.onnx`. Do not load PyTorch `.pt` files.
2. **Single Worker**: Ensure `uvicorn` runs with `--workers 1`.
3. **Check RSS Memory**: The backend logs RSS memory at boot and after each prediction:
   ```
   [Memory] Process RSS: 78.4 MB (Peak: 81.2 MB)
   ```
   Typical steady-state footprint is **~80-140 MB**, well below the 512 MB ceiling.
4. **Ephemeral Data Reset**: Uploaded images and reports reset when the container restarts. For persistent storage in high-traffic deployments, attach a Render Disk or cloud object storage (S3/GCS).
