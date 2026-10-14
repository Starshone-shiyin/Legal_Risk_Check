import unittest
from pathlib import Path


class DocumentUploadFrontendContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.script = (root / "web" / "app.js").read_text(encoding="utf-8")
        cls.styles = (root / "web" / "styles.css").read_text(encoding="utf-8")

    def test_chat_composer_accepts_pasted_images_through_the_shared_upload_path(self):
        self.assertIn('input.addEventListener("paste", handleChatImagePaste)', self.script)
        self.assertIn("async function handleChatImagePaste(event)", self.script)
        self.assertIn("await uploadChatFiles([new File([image], filename", self.script)
        self.assertIn("async function uploadChatFile(file, { clearErrors = true } = {})", self.script)
        self.assertIn('document.querySelector(".chat-input .send-button")', self.script)

    def test_chat_composer_accepts_dragged_files_with_a_visible_drop_state(self):
        self.assertIn('setupChatFileDropzone(dropTarget)', self.script)
        self.assertIn('dropTarget.addEventListener("drop", async (event)', self.script)
        self.assertIn("await uploadChatFiles(Array.from(event.dataTransfer.files || []))", self.script)
        self.assertIn("async function uploadChatFiles(files)", self.script)
        self.assertIn("chat-panel.dragging-files .chat-drop-overlay", self.styles)

    def test_attachment_labels_cover_all_supported_chat_format_groups(self):
        for marker in ('"docx"', '"xlsx"', '"pptx"', '"csv"', '"jp2"', '"bmp"', '"txt"', '"md"'):
            self.assertIn(marker, self.script)
        self.assertIn("attachment-file-icon.type-text", self.styles)


if __name__ == "__main__":
    unittest.main()
