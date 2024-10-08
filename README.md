# Poetry-Data-Work
### 📖 Python + PostgreSQL: 
A functional data workflow covering all stages from extraction to visualization.

## Data Sourcing
### Introduction to the API used:

PoetryDB is a free API for accessing poetry data. It offers a large collection of poems, which can be searched by author, title, or lines, with results in JSON format. The API is built in Ruby using Sinatra for routes, and the data is stored in a MongoDB database.

<div align="center">
<img src="readme-pics/PoetryDB.png" width="400" />
<br/>
Source: https://github.com/thundercomb/poetrydb
</div>


### Justification of my selection:
* PoetryDB has been consistently maintained by its creator and is open-source, so it is a reliable and stable API for research. 
* The database is extensive and accurate enough to support meaningful analysis. Specifically, it includes 129 authors, 3010 poems and 254053 lines data.

## Data Ingestion
### Data Flow
* Fetching and Inserting Authors:
    <br/>a.	Sending a request to retrieve a list of authors (get_authors()).
    <br/>b.	Storing these authors in the authors table using insert_authors().
* Fetching Titles:
  <br/>a.	Sending another request to get a list of poem titles (get_titles()).
  <br/>b.	For each title, fetching detailed information about the poem, including the author, title, line count, and the poem's content (get_poem_by_title()).
* Inserting Poems:
  <br/>a.	Inserting poems data into the poems table using insert_poem(). The corresponding author is fetched from the authors table to maintain the relationship between the poem and its author.
  <br/>b.	If a poem is already in the database, the script skips inserting it again.
* Inserting Poem Lines:
  <br/>a.	The lines of each poem are stored in the lines table using insert_lines(). Each line of the poem is linked to its corresponding poem_id, and each line is given a line number to preserve the order of the poem's content.

### Database Schema
 
<div align="center">
<img src="readme-pics/DB-Schema.jpg" width="700"/>
<br/>
Database Schema
</div>


Constraints:
<br/>
Unique constraints on author_name, poem_title and line_id ensure that there are no duplicates in the database. Foreign keys like author_id and poem_id constraints ensure data integrity by linking poems to valid authors and lines to valid poems.

## Data Cleaning and Processing
* Removing Duplicate Poems:
Used SQL with the poem_title unique constraint and ON CONFLICT DO NOTHING clause to filter out the duplicates, leaving 2727 unique poems in the database.
* Cleaning Poem Titles and Line Content:
Titles like 'Twould ease -- a Butterfly -- contains unnecessary quotes or symbols at the beginning or end. I used regular expressions in Python to clean these titles. For line content cleaning, I also removed extra spaces and meaningless symbols by using regular expressions. After the cleaning step, I removed 19 empty lines from the database.

## Exploratory Data Analysis and Insights
* Distribution of poem lengths:
<div align="center">
<img src="readme-pics/EDA-1.png" width="200" />
<br/>Insights: Most of the poems have 5-14 lines.
</div>

* Top 10 most productive authors:
<div align="center">
<img src="readme-pics/EDA-2.png" width="200" />
<br/>Insights: Despite having 129 authors, the top 10 authors with the highest output account for more than half of the total number of poems (1534 out of 2727).
</div>

* Frequency of time-related words in poems:
<div align="center">
<img src="readme-pics/EDA-3.png" width="180" />
<br/>Insights: The word 'may,' which can also mean 'might,' is the most frequent time-related word in the poems, followed by 'night.'
</div>

* Top 20 most frequent words (potential themes) across all poems:
<div align="center">
<img src="readme-pics/EDA-4.png" width="170" />
<br/>Insights: Combined natural language toolkit (nltk) library and my own custom stopwords to remove many meaningless stopwords. The top three words in the ranking list that can be potential themes are “love”, “heart” and “god”.
</div>

## Visualization 
* Distribution of poem lengths [Pie Chart]
* Pie chart visualized how various poem length ranges contribute to the overall dataset.
<div align="center">
<img src="visualization-pics/poem_length_distribution.png" width="600" />
</div>
 
* Top 10 most productive authors [Horizontal Bar Chart]
* Horizontal bar charts are excellent for comparing categories.
<div align="center">
<img src="visualization-pics/top_10_productive_authors.png" width="600" />
</div>
 
* Time-related words frequency [Treemap]
* The size of each rectangle in a treemap corresponds to the frequency of the words. This makes it easy to compare the relative frequencies of different time-related words at a glance.
<div align="center">
<img src="visualization-pics/time_related_words_treemap.png" width="600" />
</div>

* Top 50 most common words [Word Cloud]
* A word cloud visually emphasizes the most frequent words by displaying them in varying sizes.
<div align="center">
<img src="visualization-pics/top_50_words_wordcloud.png" width="600" />
</div>

* Correlation between poem length and word diversity [Scatter plot]
<div align="center">
<img src="readme-pics/query.jpg" width="509" />
</div>
* There is only one poem record that has more than 5000 lines, so to better analyze correlation between poem length and word diversity, I ignored this record.<br/>
Poem length and word diversity are two continuous variables. A scatter plot is ideal for clearly displaying the relationship between them.
<div align="center">
<img src="visualization-pics/poem_length_word_diversity.png" width="600" />
</div>

## Anti-Plagiarism Notice

Please note that the code and content in this project are intended for educational and reference purposes only. Any form of plagiarism or unauthorized use will be considered a violation of academic integrity. Ensure you comply with relevant academic and legal standards before using this material. You should not copy this project as your assignment. The consequences of any misuse are the sole responsibility of the user.