import os
import io
import tempfile
from typing import List, Tuple
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader


class DocumentLoader:
    def __init__(self, directory: str = ""):
        self.directory = directory

    def load_files(self) -> List[str]:
        """
        Loads all supported files from the directory and returns their content.
        """
        contents = []
        if not os.path.exists(self.directory):
            return ["Directory not found."]

        for filename in os.listdir(self.directory):
            filepath = os.path.join(self.directory, filename)
            content = ""

            try:
                if filename.endswith(".pdf"):
                    loader = PyPDFLoader(filepath)
                    pages = loader.load()
                    content = "\n\n".join([p.page_content for p in pages])
                elif filename.endswith(".docx") or filename.endswith(".doc"):
                    loader = UnstructuredWordDocumentLoader(filepath)
                    docs = loader.load()
                    content = "\n\n".join([d.page_content for d in docs])
                elif filename.endswith(".txt") or filename.endswith(".md"):
                    loader = TextLoader(filepath)
                    docs = loader.load()
                    content = docs[0].page_content
                else:
                    continue

                if content:
                    contents.append(f"--- File: {filename} ---\n{content}\n")
            except Exception as e:
                contents.append(f"--- Error loading {filename}: {str(e)} ---\n")

        return contents

    @staticmethod
    def load_from_bytes(files: List[Tuple[str, bytes]]) -> List[str]:
        """
        Accepts a list of (filename, bytes_content) tuples and returns list of content strings.
        Useful for cloud/Streamlit uploads where files are in-memory.
        """
        contents = []
        for filename, file_bytes in files:
            try:
                if filename.endswith(".txt") or filename.endswith(".md"):
                    content = file_bytes.decode("utf-8", errors="replace")
                elif filename.endswith(".pdf") or filename.endswith(".docx") or filename.endswith(".doc"):
                    # Write to temp file for loaders that require file paths
                    suffix = os.path.splitext(filename)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(file_bytes)
                        tmp_path = tmp.name
                    try:
                        if filename.endswith(".pdf"):
                            loader = PyPDFLoader(tmp_path)
                            pages = loader.load()
                            content = "\n\n".join([p.page_content for p in pages])
                        else:
                            loader = UnstructuredWordDocumentLoader(tmp_path)
                            docs = loader.load()
                            content = "\n\n".join([d.page_content for d in docs])
                    finally:
                        os.unlink(tmp_path)
                else:
                    continue

                if content:
                    contents.append(f"--- File: {filename} ---\n{content}\n")
            except Exception as e:
                contents.append(f"--- Error loading {filename}: {str(e)} ---\n")
        return contents


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        loader = DocumentLoader(sys.argv[1])
        print(loader.load_files())
