import pyodbc
import streamlit as st
import pandas as pd
import numpy as np
import re
from gensim.models import Word2Vec
from sklearn.neighbors import NearestNeighbors
import fitz  # PyMuPDF

# Title and header
st.set_page_config(page_title="BOOK RECOMMENDATION SYSTEM", layout="wide")
st.markdown("""
<style>
h1 {
    text-align: center;
    color: red;
}
</style>
# Book Recommendation System
""", unsafe_allow_html=True)

# Database connection
server = 'VoHuuNghia'
database = 'library_warehouse'
driver = '{ODBC Driver 17 for SQL Server}'
connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;"

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    cursor.execute("SELECT @@version;")
    row = cursor.fetchone()

    getBookQuery = "SELECT * FROM DimBook"
    df_Book = pd.read_sql(getBookQuery, conn)
    conn.close()  # Close connection after fetching data
except pyodbc.Error as e:
    st.error(f"Error connecting to SQL Server: {e}")

# Function to clean book names
def clean_name(tailieu_name):
    match = re.search(r'\$a([^$]*)', tailieu_name)
    if match:
        clean_name = match.group(1).strip()
        clean_name = re.sub(r'[/:]', '', clean_name).lower()
        return clean_name
    return tailieu_name

if 'visibility' not in st.session_state:
    st.session_state.visibility = 'visible'
if 'disabled' not in st.session_state:
    st.session_state.disabled = False
if 'placeholder' not in st.session_state:
    st.session_state.placeholder = ''

col1, col2 = st.columns(2)

with col1:
    text_input_1 = st.text_input(
        "Enter Book Name 👇",
        label_visibility=st.session_state.visibility,
        disabled=st.session_state.disabled,
        placeholder=st.session_state.placeholder,
        help="Start typing to see book name suggestions"
    )

df_Book['Tailieu_Name'] = df_Book['Tailieu_Name'].apply(clean_name)
sentences = df_Book['Tailieu_Name'].apply(lambda x: x.split()).tolist()

model = Word2Vec(sentences, vector_size=100, window=5, min_count=1, workers=4)

def vectorize_sentence(sentence, model):
    words = sentence.split()
    word_vectors = [model.wv[word] for word in words if word in model.wv]
    if len(word_vectors) == 0:
        return np.zeros(model.vector_size)
    return np.mean(word_vectors, axis=0)

df_Book['vector'] = df_Book['Tailieu_Name'].apply(lambda x: vectorize_sentence(x, model))
X = np.vstack(df_Book['vector'].values)
knn = NearestNeighbors(n_neighbors=5, metric='cosine')
knn.fit(X)

def recommend_books(keyword):
    keyword_cleaned = re.sub(r'[/:]', '', keyword.lower())
    keyword_vector = vectorize_sentence(keyword_cleaned, model)
    distances, indices = knn.kneighbors([keyword_vector])
    recommendations = df_Book.iloc[indices.flatten()]['Tailieu_Name'].tolist()
    return recommendations

if text_input_1:

    recommendations = recommend_books(text_input_1)
    if recommendations:
        st.subheader("Recommended books:")
        for book in recommendations:
            st.write(book)
    else:
        st.write("No recommendations found for the entered book name.")
else:
    st.write("Please enter a book name in the input field.")

def pdf_to_images(pdf_path):
    doc = fitz.open(pdf_path)
    images = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img = pix.tobytes("png")
        images.append(img)
    return images

def main():
    st.title("GENERATING STATISTICAL GRAPHS")

    pdf_path = r"D:\A-DO-AN\RECOMMEND_SYSTEMS\RS\library_warehouse.pdf"

    titles = [
        "Thống kê số lượng sinh viên đã mượn sách theo từng khoa",
        "Số lượng sinh viên đã mượn sách qua các năm",
        "Thống kê số sách được mượn theo từng khoa",
        "Top 5 sách được mượn nhiều nhất theo từng khoa",
        "Top 10 sách giáo trình được mượn nhiều nhất ở mỗi CTDT",
        "Thống kê số lượng sách phục vụ cho từng trình độ",
        "Số lượng sinh viên sử dụng thư viện",
        "Tổng số của ma xếp giá theo ID tài liệu"
    ]
    
    if pdf_path:
        images = pdf_to_images(pdf_path)
        selected_title = st.selectbox("Chọn biểu đồ để hiển thị", titles)
        selected_index = titles.index(selected_title)
        
    if selected_index < len(images):
        st.image(images[selected_index], use_column_width=True)
    else:
        st.write("Không tìm thấy trang tương ứng trong PDF.")

if __name__ == "__main__":
    main()