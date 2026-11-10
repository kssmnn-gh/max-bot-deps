"""Run inside the dependency image before publishing; no keys or network calls."""
import importlib.metadata
import subprocess
import tempfile
from pathlib import Path

import chromadb
import pytesseract
import sentence_transformers
import torch
from docx import Document
from playwright.sync_api import sync_playwright

assert {'rus', 'eng'} <= set(pytesseract.get_languages())
assert torch.__version__ == '2.5.1+cpu'
assert torch.ones(2).sum().item() == 2
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    document = Document()
    document.add_paragraph('Проверка преобразования документа / Document check')
    document.save(root / 'probe.docx')
    subprocess.run(['libreoffice', '-env:UserInstallation=file:///tmp/base-image-lo-profile',
                    '--headless', '--convert-to', 'pdf', '--outdir', str(root),
                    str(root / 'probe.docx')], check=True, timeout=60)
    assert (root / 'probe.pdf').read_bytes().startswith(b'%PDF-')
    client = chromadb.PersistentClient(path=str(root / 'chroma'))
    collection = client.create_collection('smoke')
    collection.add(ids=['one'], embeddings=[[1., 0.]], documents=['probe'])
    assert collection.query(query_embeddings=[[1., 0.]], n_results=1)['ids'] == [['one']]
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_content('<p>Браузер работает</p>')
    assert page.locator('p').inner_text() == 'Браузер работает'
    browser.close()
for package in ('torch', 'chromadb', 'sentence-transformers', 'playwright', 'Flask', 'gunicorn'):
    print(package, importlib.metadata.version(package))
print('Dependency image smoke checks passed')
