def save_pdf_to_text(pdf_path, pdf_text):

    pdf_path = f"{pdf_path}.txt"

    with open(pdf_path, "w") as f:
        f.write(pdf_text)

    logging.info(f"Saved PDF to {pdf_path}")

