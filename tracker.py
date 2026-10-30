# from docx import Document
# import difflib
# import matplotlib.pyplot as plt
# from collections import Counter
# import nltk
# from sklearn.feature_extraction.text import TfidfVectorizer
# import string
# import re

# nltk.download('punkt')
# nltk.download('stopwords')
# from nltk.corpus import stopwords

# def extract_text_from_docx(path):
#     doc = Document(path)
#     return "\n".join([para.text for para in doc.paragraphs])

# def preprocess(text):
#     text = text.lower()
#     text = re.sub(r'\d+', '', text)
#     text = text.translate(str.maketrans('', '', string.punctuation))
#     words = nltk.word_tokenize(text)
#     return [word for word in words if word not in stopwords.words('english')]

# def get_keyword_diff(text1, text2, top_n=20):
#     vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
#     vectors = vectorizer.fit_transform([text1, text2])
#     keywords1 = set(vectorizer.get_feature_names_out())
#     return keywords1

# def diff_texts(text1, text2):
#     diff = difflib.unified_diff(
#         text1.splitlines(),
#         text2.splitlines(),
#         lineterm='',
#         fromfile='Old Resume',
#         tofile='New Resume'
#     )
#     return '\n'.join(diff)

# def plot_keyword_comparison(text1, text2):
#     words1 = preprocess(text1)
#     words2 = preprocess(text2)
#     count1 = Counter(words1)
#     count2 = Counter(words2)

#     common = set(count1.keys()).union(set(count2.keys()))
#     data = {'keywords': [], 'v1': [], 'v2': []}
#     for word in common:
#         data['keywords'].append(word)
#         data['v1'].append(count1.get(word, 0))
#         data['v2'].append(count2.get(word, 0))

#     plt.figure(figsize=(12, 6))
#     indices = range(len(data['keywords']))
#     plt.bar(indices, data['v1'], width=0.4, label='Version 1', align='center')
#     plt.bar([i + 0.4 for i in indices], data['v2'], width=0.4, label='Version 2', align='center')
#     plt.xticks([i + 0.2 for i in indices], data['keywords'], rotation=90)
#     plt.title('Keyword Usage Comparison')
#     plt.legend()
#     plt.tight_layout()
#     plt.show()

# # === RUN THE TOOL ===

# text_v1 = extract_text_from_docx('resume_v1.docx')
# text_v2 = extract_text_from_docx('resume_v2.docx')

# print("🔍 Text Differences:")
# print(diff_texts(text_v1, text_v2))

# print("\n📊 Keyword Comparison Plot:")
# plot_keyword_comparison(text_v1, text_v2)


import difflib
import os

def compare_resume_versions(file1_path, file2_path):
    """
    Compares two text files representing resume versions and prints the differences.

    Args:
        file1_path (str): The path to the first resume file (text).
        file2_path (str): The path to the second resume file (text).
    """
    try:
        with open(file1_path, 'r', encoding='utf-8') as file1, \
             open(file2_path, 'r', encoding='utf-8') as file2:
            file1_lines = file1.readlines()
            file2_lines = file2.readlines()

        differ = difflib.unified_diff(
            file1_lines,
            file2_lines,
            fromfile=file1_path,
            tofile=file2_path,
            lineterm='' # Important to avoid extra newlines in output
        )

        print(f"Comparing '{os.path.basename(file1_path)}' and '{os.path.basename(file2_path)}':")
        print("-" * 30)
        for line in differ:
            # Basic highlighting based on diff indicators
            if line.startswith('+ '):
                print(f"\033[92m{line}\033[0m", end='') # Green for added lines
            elif line.startswith('- '):
                print(f"\033[91m{line}\033[0m", end='') # Red for deleted lines
            elif line.startswith('? '):
                 print(f"\033[94m{line}\033[0m", end='') # Blue for lines with intra-line changes (approximate)
            else:
                print(line, end='') # No color for common lines or diff headers
        print("-" * 30)

    except FileNotFoundError:
        print("Error: One or both files not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

# --- How to use ---

# Create dummy resume text files for demonstration
resume1_content = """John Doe
Email: john.doe@email.com
Phone: 123-456-7890

Summary
Experienced software engineer with 5 years of experience.

Experience
Software Engineer, Tech Company A (2018-Present)
- Developed and maintained web applications.
- Collaborated with cross-functional teams.

Education
Bachelor of Science in Computer Science, University A (2014-2018)

Skills
Python, Java, SQL, JavaScript
"""

resume2_content = """John Doe
Email: john.doe.new@email.com
Phone: 987-654-3210

Summary
Highly motivated and experienced software engineer with 6 years of experience.

Experience
Senior Software Engineer, Tech Company B (2021-Present)
- Led a team in developing scalable microservices.
- Implemented CI/CD pipelines.
Software Engineer, Tech Company A (2018-2021)
- Developed and maintained web applications.
- Collaborated with cross-functional teams.

Education
Bachelor of Science in Computer Science, University A (2014-2018)
Master of Science in Software Engineering, University B (2021-2023)

Skills
Python, Java, SQL, JavaScript, Docker, Kubernetes
"""

with open("resume_v1.txt", "w", encoding='utf-8') as f:
    f.write(resume1_content)

with open("resume_v2.txt", "w", encoding='utf-8') as f:
    f.write(resume2_content)

# Compare the two dummy files
compare_resume_versions("resume_v1.txt", "resume_v2.txt")

# Clean up dummy files (optional)
# import os
# os.remove("resume_v1.txt")
# os.remove("resume_v2.txt")