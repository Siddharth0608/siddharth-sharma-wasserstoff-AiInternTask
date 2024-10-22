# Overview
This program extracts text, keywords, and summaries from PDF files in a specified folder. It then stores the extracted data in a MongoDB database. The project uses several libraries, including pdfplumber, nltk, and pymongo, to accomplish its tasks.

# Requirements
Before running the program, ensure you have the following installed:

Python 3.x

Libraries: You can install the required libraries using pip:

### !pip install pdfplumber pymongo scikit-learn nltk
MongoDB: You need to have access to a MongoDB database. Replace the connection URI in the code with your own database URI.

# How to Run the Program
Download the Code: Make sure you have the complete code saved in a Python file, for example, pdf_metadata_extractor.py.

Prepare Your PDFs: Place all your PDF files in a folder on your machine. Update the pdf_folder_path variable in the code to point to this folder.

Set Up MongoDB: Ensure your MongoDB database is running and accessible. Update the MongoDB connection URI in the code to match your MongoDB setup.

Run the Code: Open your terminal or command prompt, navigate to the folder containing the Python file, and run:

python pdf_metadata_extractor.py
Check the Output: After running the program, the extracted data will be stored in the MongoDB collection specified in the code. You can also see the printed output of all data retrieved from the database.

# Notes
I wasn't able to create a Docker file for this project due to previous attempts that resulted in my laptop crashing. My laptop's resources are limited, and running Docker often consumes significant memory and processing power, leading to instability. Despite my efforts to optimize the setup, the performance constraints of my system prevented me from successfully configuring a Docker environment.

Additionally, I faced challenges in hosting this program on Streamlit. The processing involved in generating summaries and extracting keywords from multiple PDF files is resource-intensive, which slowed down the performance of my laptop. Given the tight timeline I was working under, I could not afford the time required to troubleshoot and resolve these performance issues. As a result, I had to prioritize getting the core functionality of the program working locally rather than exploring deployment options.

# Extracted Data from the PDFs
I have attached a JSON file containing the extracted data from the PDF files processed by the program on my laptop. This JSON file includes all the essential information, such as:

PDF Name: The name of each PDF file.
PDF Size: The size of each PDF file.
PDF Path: The file path to each PDF.
PDF Summary: A concise summary extracted from the content of each PDF.
PDF Keywords: A list of relevant keywords identified from each PDF.

# Troubleshooting
If you encounter any issues, check the following:

Ensure all libraries are installed correctly.
Make sure the MongoDB connection URI is valid.
Verify that the path to your PDF folder is correct.
If you have any questions or need further assistance, feel free to reach out!






 
