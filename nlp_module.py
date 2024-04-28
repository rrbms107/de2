import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import re
import tensorflow as tf
from transformers import AutoTokenizer, TFRobertaModel
import spacy

nltk.download('punkt')
nltk.download('stopwords')

def extract_keywords(paragraph, num_keywords=15):
    # Tokenization
    words = word_tokenize(paragraph)

    # Remove non-alphanumeric tokens (symbols and punctuation)
    words = [word.lower() for word in words if re.match('^[a-zA-Z0-9]+$', word)]

    # Stopword Removal
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word not in stop_words]

    # Stemming (you can also use lemmatization if needed)
    stemmer = PorterStemmer()
    words = [stemmer.stem(word) for word in words]

    # Return a specified number of keywords
    return words[:num_keywords]

def compare_texts(paragraph1, paragraph2, keywordsA, keywordsB):
    nlp = spacy.load('en_core_web_sm')
    # Preprocess the paragraphs using Spacy
    doc1 = nlp(paragraph1)
    doc2 = nlp(paragraph2)

    # Extract the keywords from the two paragraphs
    keywords1 = [token.lemma_ for token in doc1 if (not token.is_stop) and (not token.is_punct) and (token.lemma_ in keywordsA)]
    keywords2 = [token.lemma_ for token in doc2 if (not token.is_stop) and (not token.is_punct) and (token.lemma_ in keywordsB)]

    # Compare the keyword sets and calculate the keyword similarity
    union_keywords = set(keywords1) | set(keywords2)
    intersection_keywords = set(keywords1) & set(keywords2)
    if union_keywords:
        keyword_similarity = len(intersection_keywords) / len(union_keywords) * 100
    else:
        keyword_similarity = 0

    # Load the tokenizer and model for computing embeddings and similarity
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/paraphrase-distilroberta-base-v1")
    model = TFRobertaModel.from_pretrained("sentence-transformers/paraphrase-distilroberta-base-v1")

    # Tokenize the paragraphs
    inputs1 = tokenizer(paragraph1, return_tensors='tf', padding=True, truncation=True, max_length=512)
    inputs2 = tokenizer(paragraph2, return_tensors='tf', padding=True, truncation=True, max_length=512)

    # Calculate the embeddings for the two paragraphs
    embeddings1 = model(**inputs1).last_hidden_state
    embeddings2 = model(**inputs2).last_hidden_state

    # Calculate the cosine similarity
    # Note: The embeddings are normalized to unit length before computing the cosine similarity
    embeddings1_norm = tf.nn.l2_normalize(embeddings1, axis=1)
    embeddings2_norm = tf.nn.l2_normalize(embeddings2, axis=1)
    cosine_similarity = tf.reduce_sum(tf.multiply(embeddings1_norm, embeddings2_norm), axis=1)
    cosine_similarity = 100 * cosine_similarity

    # Calculate the average cosine similarity
    avg_cosine_similarity = tf.reduce_mean(cosine_similarity)

    # Calculate the overall similarity
    overall_similarity = 0.5 * (cosine_similarity + keyword_similarity)

    # Calculate the average overall similarity
    avg_overall_similarity = tf.reduce_mean(overall_similarity)

    return avg_cosine_similarity, avg_overall_similarity, keyword_similarity

def compare_and_extract_keywords(paragraph1, paragraph2):
    # Extract keywords from the paragraphs
    keywords1 = extract_keywords(paragraph1, num_keywords=15)
    keywords2 = extract_keywords(paragraph2, num_keywords=15)

    # Compare the texts and extract similarities
    avg_cosine_similarity, avg_overall_similarity, keyword_similarity = compare_texts(paragraph1, paragraph2, keywords1, keywords2)

    # Return the results
    return {
        'keywords1': keywords1,
        'keywords2': keywords2,
        'cosine_similarity': avg_cosine_similarity.numpy().tolist(),
        'overall_similarity': avg_overall_similarity.numpy().tolist(),
        'keyword_similarity': keyword_similarity
    }
