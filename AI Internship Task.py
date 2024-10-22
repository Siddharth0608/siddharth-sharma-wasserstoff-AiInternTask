# -*- coding: utf-8 -*-
"""
Created on Mon Oct 21 23:13:17 2024

@author: sid
"""

import os
import pdfplumber
from concurrent.futures import ThreadPoolExecutor, as_completed
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
nltk.download('stopwords', quiet = True)
nltk.download('punkt', quiet = True)
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import errors

class config:
    # MongoDb configuration class
    URI = "mongodb+srv://siddharthsharma2002:095smhRdo44idLfa@pdfs-database-collectio.v06od.mongodb.net/?retryWrites=true&w=majority&appName=PDFs-Database-Collection"
    DB_NAME = "PDFs-Data"
    COLLECTION_NAME = "PDFs-Dataset"

class MongoDBHandler:
    def __init__(self, config_file = "C:\\Users\\siddh\\Downloads\\config.json"):
        # Load the MongoDB config class
        CONFIG = config()
        self.uri = CONFIG.URI  # MongoDB URI
        self.db_name = CONFIG.DB_NAME  # Database name
        self.collection_name = CONFIG.COLLECTION_NAME  # Collection name
        self.client = None
        self.db = None
        self.collection = None
        self._connect()  # Connect to the database

    def _connect(self):
        # Establish a connection with MongoDB
        try:
            self.client = MongoClient(self.uri, server_api=ServerApi('1'))
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            self.client.admin.command('ping')  # Test connection
            print("Successfully connected to MongoDB!")
        except errors.ConnectionFailure as e:
            print(f"Failed to connect to MongoDB: {e}")
            
    def get_all_data(self):
        # Retrieve all documents from the collection and return them as a list of dictionaries
        try:
            all_data = list(self.collection.find({}))  # Retrieve all documents
            for document in all_data:
                document['_id'] = str(document['_id'])  # Convert ObjectId to string
            return all_data  # Return the documents as a list of dictionaries
        except errors.PyMongoError as e:
            print(f"Error retrieving data from MongoDB: {e}")
            return []

    def add_metadata(self, data: dict):
        # Insert initial metadata for each PDF
        try:
            result = self.collection.insert_one(data)
            print(f"Inserted document with ID: {result.inserted_id}")
            return result
        except errors.PyMongoError as e:
            print(f"Error inserting initial data: {e}")
            return None

    def update_with_summary_and_keywords(self, pdf_name: str, summary: str, keywords: list):
        # Update the document with the extracted summary and keywords
        try:
            result = self.collection.update_one(
                {"pdf_name": pdf_name},
                {"$set": {"summary": summary, "keywords": keywords}},
                upsert=False  # Only update existing records
            )
            if result.matched_count > 0:
                print(f"Updated document with ID: {pdf_name}")
            else:
                print(f"No document found with ID: {pdf_name}")
            return result
        except errors.PyMongoError as e:
            print(f"Error updating document with summary and keywords: {e}")
            return None

    def close(self):
        # Close MongoDB connection
        if self.client:
            self.client.close()
            print("Closed MongoDB connection.")
            

class PDFScraper:
    def __init__(self, pdf_folder_path):
        # Initialize with the path to the folder containing PDFs
        self.pdf_folder_path = pdf_folder_path
        self.mongo = MongoDBHandler()

    def extract_text(self, pdf_path, pdf_name):
        # Extract text from a single PDF
        try:
            pdf_size = os.path.getsize(pdf_path)  # Get PDF file size
            metadata = {
                'pdf_path': pdf_path,
                'pdf_name': pdf_name,
                'pdf_size': pdf_size
            }
            self.mongo.add_metadata(metadata)  # Add metadata to MongoDB
            with pdfplumber.open(pdf_path) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text()  # Extract text from each page
            return text
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return None

    def process_single_pdf(self, file_path):
        # Process each individual PDF
        print(f"Processing {file_path}...")
        filename = os.path.basename(file_path)  # Get just the file name
        return filename, self.extract_text(file_path, filename)

    def process_pdfs_concurrently(self, max_workers=4):
        # Process all PDFs in the folder using multiple threads
        pdf_texts = {}
        pdf_files = [os.path.join(self.pdf_folder_path, filename) for filename in os.listdir(self.pdf_folder_path) if filename.endswith('.pdf')]
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(self.process_single_pdf, pdf_file): pdf_file for pdf_file in pdf_files}
            for future in as_completed(future_to_file):
                pdf_file = future_to_file[future]
                try:
                    filename, text = future.result()
                    if text:
                        pdf_texts[filename] = text  # Store extracted text for each PDF
                    else:
                        print(f"Failed to extract text from {filename}")
                except Exception as e:
                    print(f"Error processing {pdf_file}: {e}")
        self.mongo.close()
        return pdf_texts


class SummaryAndKeywordGenerator:
    
    def __init__(self, pdf_folder_path):
        # Initialize the scraper and process all PDFs in the folder
        self.scraper = PDFScraper(pdf_folder_path)
        self.pdf_texts = self.scraper.process_pdfs_concurrently()
        self.mongo = MongoDBHandler()

    def extract_keywords(self, num_keywords=10):
        # Extract keywords from all the PDF texts
        documents = list(self.pdf_texts.values())  # Get the texts of all PDFs
        file_paths = list(self.pdf_texts.keys())  # Get their file paths
        tfidf_vectorizer = TfidfVectorizer(stop_words='english', max_df=0.85, min_df=0.01)
        tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
        feature_names = tfidf_vectorizer.get_feature_names_out()
        all_keywords = {}
        
        for doc_idx, doc in enumerate(documents):
            scores = tfidf_matrix[doc_idx].toarray().flatten()  # Calculate TF-IDF scores
            sorted_indices = scores.argsort()[::-1]  # Sort by score
            top_keywords = [feature_names[i] for i in sorted_indices[:num_keywords]]
            all_keywords[file_paths[doc_idx]] = top_keywords  # Store top keywords
        return all_keywords

    def split_into_sentences(self, text):
        # Split text into sentences
        sentences = nltk.sent_tokenize(text)
        return sentences
    
    def calculate_word_frequencies(self, text):
        # Calculate word frequencies, ignoring stop words
        stop_words = set(stopwords.words('english'))
        words = word_tokenize(text.lower())
        words = [word for word in words if word not in stop_words and word not in string.punctuation]
        word_frequencies = {}
        for word in words:
            if word not in word_frequencies:
                word_frequencies[word] = 1
            else:
                word_frequencies[word] += 1 
        return word_frequencies
    
    def score_sentences(self, sentences, word_frequencies):
        # Score sentences based on word frequencies
        sentence_scores = {}
        for sentence in sentences:
            for word in word_tokenize(sentence.lower()):
                if word in word_frequencies:
                    if sentence not in sentence_scores:
                        sentence_scores[sentence] = word_frequencies[word]
                    else:
                        sentence_scores[sentence] += word_frequencies[word]
        return sentence_scores
    
    def generate_summary(self, sentence_scores, summary_length):
        # Select top sentences for the summary
        sorted_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)
        summary_sentences = sorted_sentences[:summary_length]
        return ' '.join(summary_sentences)
    
    def generate_extractive_summary(self):
        # Create extractive summary for all PDFs
        summaries = {}
        for pdf_name in self.pdf_texts:
            sentences = self.split_into_sentences(self.pdf_texts[pdf_name])
            summary_length = len(sentences) * 20 // 100  # setting the summary length to 20% of the extracted text
            word_frequencies = self.calculate_word_frequencies(self.pdf_texts[pdf_name])
            sentence_scores = self.score_sentences(sentences, word_frequencies)
            summary = self.generate_summary(sentence_scores, summary_length)
            summaries[pdf_name] = summary
        return summaries

    def generate_summary_and_keywords(self):
        # Generate both summaries and keywords
        summaries = self.generate_extractive_summary()
        keywords = self.extract_keywords()
        return summaries, keywords
        
    def update_database(self):
        # Update MongoDB with summaries and keywords
        summaries, keywords = self.generate_summary_and_keywords()
        for pdf_name in self.pdf_texts:
            self.mongo.update_with_summary_and_keywords(pdf_name=pdf_name, summary=summaries[pdf_name], keywords=keywords[pdf_name])
        self.mongo.close()

class PDFPipeline:
    def __init__(self, pdf_folder_path):    
        pipeline = SummaryAndKeywordGenerator(pdf_folder_path)
        pipeline.update_database()
        
        # Retrieve all data from MongoDB
        mongo_handler = MongoDBHandler()
        all_data = mongo_handler.get_all_data()
        
        # You can now work with the retrieved data
        print(all_data)
        
        
if __name__ == "__main__":
    pdf_folder_path = 'C:\\Users\\siddh\\Downloads\\pdfs'
    pipeline = PDFPipeline(pdf_folder_path)
