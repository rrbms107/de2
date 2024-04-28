import os

def get_pdf_path(folder_name, filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
    pdf_path = os.path.join(base_dir, 'pdfs', folder_name, filename)
    return pdf_path

def read_pdf_content(pdf_path):
    # Read and return the content of the PDF file
    with open(pdf_path, 'rb') as file:
        pdf_content = file.read()
    return pdf_content


# mongodb+srv://pranavdeepak2002:pannu2002@cluster0.q3ftkjf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
