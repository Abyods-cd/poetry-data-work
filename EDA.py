import psycopg2
import pandas as pd
# use the natural language toolkit library to remove stopwords
import nltk
from nltk.corpus import stopwords

DB_PARAMS = {
    'dbname': 'poetry',
    'user': '',
    'host': 'localhost',
    'port': '5432'
}

def execute_query(query):
    conn = psycopg2.connect(**DB_PARAMS)
    return pd.read_sql_query(query, conn)


def advanced_poetry_database_eda():
    print("Performing Advanced Exploratory Data Analysis on Poetry Database")

    # 1. poems length distribution analysis
    poem_length_distribution = execute_query("""
            SELECT 
                CASE 
                    WHEN line_count <= 4 THEN 'Very Short (1-4 lines)'
                    WHEN line_count <= 14 THEN 'Short (5-14 lines)'
                    WHEN line_count <= 30 THEN 'Medium (15-30 lines)'
                    WHEN line_count <= 50 THEN 'Long (31-50 lines)'
                    ELSE 'Very Long (50+ lines)'
                END as length_category,
                COUNT(*) as poem_count
            FROM poems
            GROUP BY length_category
            ORDER BY poem_count DESC
        """)

    print("\n1. Distribution of poem lengths:")
    print(poem_length_distribution)


    # 2. Top 10 most productive authors, by number of poems and total lines
    author_productivity = execute_query("""
        SELECT a.author_name, 
               COUNT(DISTINCT p.poem_id) as poem_count,
               SUM(p.line_count) as total_lines
        FROM authors a
        JOIN poems p ON a.author_id = p.author_id
        GROUP BY a.author_name
        ORDER BY poem_count DESC
        LIMIT 10
    """)

    print("\n2. Top 10 most productive authors:")
    print(author_productivity)

    # 3. time-related words frequency analysis
    time_references = execute_query("""
        SELECT LOWER(word) as word, COUNT(*) as frequency
        FROM poems p
        JOIN lines l ON p.poem_id = l.poem_id,
        LATERAL UNNEST(STRING_TO_ARRAY(l.line_content, ' ')) AS word
        WHERE LOWER(word) IN ('morning', 'afternoon', 'evening', 'night', 
                              'dawn', 'dusk', 'noon', 'midnight',
                              'spring', 'summer', 'autumn', 'winter',
                              'january', 'february', 'march', 'april', 'may', 'june',
                              'july', 'august', 'september', 'october', 'november', 'december')
        GROUP BY LOWER(word)
        ORDER BY frequency DESC
    """)

    print("\n3. Frequency of time-related words in poems:")
    print(time_references)


    # 4. Top 20 most common words across all poems
    # download the stopwords list
    nltk.download('stopwords')
    # get the list of stopwords
    stop_words = stopwords.words('english')
    # Escape stop words containing single quotes (replace ' with '' to avoid SQL errors)
    stop_words_escaped = [word.replace("'", "''") for word in stop_words]
    # convert the stop words list to a format that can be used in SQL queries
    stopwords_sql = "', '".join(stop_words_escaped)

    # SQL query to get the top 20 most common words across all poems
    theme_words_query = f"""
        SELECT LOWER(word) as word, COUNT(*) as frequency
        FROM poems p
        JOIN lines l ON p.poem_id = l.poem_id,
        LATERAL UNNEST(STRING_TO_ARRAY(l.line_content, ' ')) AS word
        WHERE LENGTH(word) > 2
        AND LOWER(word) NOT IN ('{stopwords_sql}', 'thy', 'thou', 'thee', 'shall', 'unto', 'thine', 'yet', 'thee', 'would', 'upon',
        'let', 'still', 'though', 'like', 'could', 'must', 'whose', 'thus', 'made', 'till', 'every', 'might', 'many', 'make', 'ever',
        'hath', 'first', 'know', 'come', 'even', 'last', 'much')
        AND LOWER(word) NOT LIKE '%''%'
        AND LOWER(word) NOT LIKE '%,'
        GROUP BY LOWER(word)
        ORDER BY frequency DESC
        LIMIT 20
    """

    theme_words = execute_query(theme_words_query)

    print("\n4. Top 20 most frequent words (potential themes) across all poems:")
    print(theme_words)



if __name__ == "__main__":
    advanced_poetry_database_eda()