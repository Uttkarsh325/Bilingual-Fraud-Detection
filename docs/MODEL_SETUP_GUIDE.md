# Advanced Model Setup Guide (Phase 3)

Due to GitHub's strict 100 MB file limit, the fine-tuned Transformer model weights (`model.safetensors`, ~255 MB) are **excluded from Git tracking**.

The configuration and tokenizer files are already included in the repository:
* `models/advanced_classifier/config.json` ✅ (already in repo)
* `models/advanced_classifier/tokenizer.json` ✅ (already in repo)
* `models/advanced_classifier/tokenizer_config.json` ✅ (already in repo)
* `models/advanced_classifier/model.safetensors` ⚠️ **(needs to be added locally)**

---

## 📥 How to Add `model.safetensors`

### Method 1: Download from Shared Colab / Google Drive (Recommended)

1. Open the shared Google Colab / Google Drive link provided by your teammate.
2. Download the `model.safetensors` file.
3. Move the downloaded file into your local project directory at:
   ```text
   Bilingual-Fraud-Detection/models/advanced_classifier/model.safetensors
   ```

> [!IMPORTANT]
> Make sure the filename is exactly `model.safetensors` (watch out for browser renames like `model (1).safetensors` or `model.safetensors.download`).

---

### Method 2: Export Directly from Google Colab

If you are running the training notebook in Google Colab:
1. Mount your Google Drive or run the training cells.
2. The notebook saves the checkpoint directory.
3. Locate `model.safetensors` in the Colab file explorer (`/content/...` or `/content/drive/MyDrive/...`).
4. Right-click `model.safetensors` > **Download**.
5. Place it in `models/advanced_classifier/`.

---

## 📁 Expected Directory Structure

Once placed, your `models/` directory should look exactly like this:

```text
Bilingual-Fraud-Detection/
└── models/
    ├── advanced_classifier/
    │   ├── config.json              <-- from Git
    │   ├── tokenizer.json           <-- from Git
    │   ├── tokenizer_config.json    <-- from Git
    │   └── model.safetensors        <-- DOWNLOADED FILE HERE (~255 MB)
    ├── advanced_xgboost.joblib
    └── baseline_tfidf.joblib
```

---

## ✅ How to Verify the Model Loads Correctly

Run this one-line check from your project root in PowerShell / terminal:

```powershell
python -c "from transformers import AutoModelForSequenceClassification; model = AutoModelForSequenceClassification.from_pretrained('models/advanced_classifier'); print('✅ Advanced Classifier loaded successfully!')"
```

If you see:
```text
✅ Advanced Classifier loaded successfully!
```
The model is properly configured and ready for inference and API serving!
