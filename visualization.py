import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from wordcloud import WordCloud
import squarify
import nltk
from nltk.corpus import stopwords
import psycopg2
from PIL import Image

DB_PARAMS = {
    'dbname': 'poetry',
    'user': '',
    'host': 'localhost',
    'port': '5432'
}

# Set the style for all plots
plt.style.use('seaborn')
sns.set_palette("deep")

def execute_query(query):
    conn = psycopg2.connect(**DB_PARAMS)
    return pd.read_sql_query(query, conn)

# 1. Distribution of poem lengths (Pie Chart)
def draw_distribution_of_poem_lengths():
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

    plt.figure(figsize=(14, 10))
    colors = ["#8ECFC9", "#FFBE7A", "#FA7F6F", "#82B0D2", "#BEB8DC" ]
    plt.pie(
        poem_length_distribution['poem_count'],
        labels=poem_length_distribution['length_category'],
        autopct='%1.1f%%',
        startangle=160,
        colors=colors,
        textprops={'fontsize': 22}
    )
    plt.title('Distribution of Poem Lengths', fontsize=28, fontweight='bold')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig('poem_length_distribution.png')
    plt.close()

# 2. Top 10 most productive authors (Horizontal Bar Chart)
def draw_top_10_most_productive_authors():
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

    plt.figure(figsize=(12, 8))
    barplot = sns.barplot(
        x='poem_count',
        y='author_name',
        data=author_productivity,
        palette='viridis',
    )
    # set the x and y labels' font size
    barplot.tick_params(axis='x', labelsize=15)
    barplot.tick_params(axis='y', labelsize=15)

    plt.title('Top 10 Most Productive Authors', fontsize=23, fontweight='bold')
    plt.xlabel('Number of Poems', fontsize=18)
    plt.ylabel('Author', fontsize=18)
    plt.tight_layout()
    plt.savefig('top_10_productive_authors.png')
    plt.close()

# 3. Time-related words frequency (Treemap)
# delete the word 'may' from the query, because it has more possibility to be recognized as "might"
def draw_time_related_words_frequency():
    time_references = execute_query("""
        SELECT LOWER(word) as word, COUNT(*) as frequency
        FROM poems p
        JOIN lines l ON p.poem_id = l.poem_id,
        LATERAL UNNEST(STRING_TO_ARRAY(l.line_content, ' ')) AS word
        WHERE LOWER(word) IN ('morning', 'afternoon', 'evening', 'night', 
                              'dawn', 'dusk', 'noon', 'midnight',
                              'spring', 'summer', 'autumn', 'winter',
                              'january', 'february', 'march', 'april', 'june',
                              'july', 'august', 'september', 'october', 'november', 'december')
        GROUP BY LOWER(word)
        ORDER BY frequency DESC
    """)

    plt.figure(figsize=(22, 14))
    color = ["#BEB8DC", "#E7DAD2", "#E7EFFA","#f2d9aa","#edfff5"]
    squarify.plot(
        sizes=time_references['frequency'],
        label=time_references['word'],
        alpha=.8,
        color=color,
        text_kwargs={'fontsize':20, 'fontweight':'bold'}
    )
    plt.title('Frequency of Time-related Words in Poems', fontsize=40, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig('time_related_words_treemap.png')
    plt.close()


# 4. Top 50 most common words (Word Cloud)
def draw_top_50_most_common_words():
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
        LIMIT 50
    """

    theme_words = execute_query(theme_words_query)
    # set the path to the image that will be used as a mask for the word cloud
    cloud_image = np.array(Image.open('./img.WEBP'))
    # use the 'Set2' colormap for the word cloud
    colormap = 'Set2'
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        mask=cloud_image,
        contour_color='white',
        contour_width=1,
        colormap=colormap
    ).generate_from_frequencies(dict(zip(theme_words['word'], theme_words['frequency'])))

    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Top 50 Most Common Words in Poems', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig('top_50_words_wordcloud.png')
    plt.close()

# 5. Correlation between poem length and word diversity (Scatter plot)
def draw_poem_length_word_diversity():
    poem_diversity = execute_query("""
        SELECT p.poem_id, p.line_count, COUNT(DISTINCT LOWER(word)) as unique_words
        FROM poems p
        JOIN lines l ON p.poem_id = l.poem_id,
        LATERAL UNNEST(STRING_TO_ARRAY(l.line_content, ' ')) AS word
        WHERE LENGTH(word) > 2
        AND line_count < 5000
        GROUP BY p.poem_id, p.line_count
    """)

    plt.figure(figsize=(10, 6))
    sns.scatterplot(x='line_count', y='unique_words', data=poem_diversity, alpha=0.6)
    plt.title('Correlation between Poem Length and Word Diversity', fontsize=16, fontweight='bold')
    plt.xlabel('Number of Lines', fontsize=12)
    plt.ylabel('Number of Unique Words', fontsize=12)
    plt.tight_layout()
    plt.savefig('poem_length_word_diversity.png')
    plt.close()


print("All visualizations have been created and saved.")

if __name__ == '__main__':
    draw_distribution_of_poem_lengths()
    draw_top_10_most_productive_authors()
    draw_time_related_words_frequency()
    draw_top_50_most_common_words()
    draw_poem_length_word_diversity()