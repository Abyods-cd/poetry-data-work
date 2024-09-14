import json
import psycopg2
import requests
import re

# set the base URL
BASE_URL = "https://poetrydb.org"

# database connection parameters
DB_PARAMS = {
    'dbname': 'poetry',
    'user': '',
    'host': 'localhost',
    'port': '5432'
}

# get authors from the API
def get_authors():
    res = requests.get(BASE_URL + "/author")
    if res.status_code == 200:
        res_data = res.json()["authors"]
        return res_data
    else:
        print("Failed to get authors: " + str(res.status_code))


# get poems' titles from the API
def get_titles():
    res = requests.get(BASE_URL + "/title")
    if res.status_code == 200:
        res_data = res.json()
        return res_data["titles"]
    else:
        print("Failed to get title: " + str(res.status_code))

# get poem data by poem title
def get_poem_by_title(title):
    res = requests.get(BASE_URL + "/title/" + title)
    if res.status_code == 200:
        res_data = res.json()
        # check if poem data is a list with only one element, if not, return None
        if isinstance(res_data, list) and len(res_data) == 1:
            if "author" not in res_data[0] or "title" not in res_data[0] or "linecount" not in res_data[0]:
                return None
            else:
                return res_data[0]
        else:
            return None
    else:
        print("Failed to get poem by title: " + str(res.status_code))
        return None

# insert authors into PostgreSQL
def insert_authors(authors):
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    for author in authors:
        cursor.execute("""
            INSERT INTO authors (author_name) VALUES (%s)
            ON CONFLICT (author_name) DO NOTHING;
        """, (author,))
    conn.commit()
    cursor.close()
    conn.close()

# insert poem into PostgreSQL
def insert_poem(poem):
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()

    try:
        # check if poem data has required fields
        if "author" not in poem or "title" not in poem or "linecount" not in poem:
            print("Poem data missing required fields")
            return None

        # get author, title, and linecount from poem data
        author_name = poem["author"]
        poem_title = poem["title"]
        line_count = poem["linecount"]

        # get author_id from authors table
        cursor.execute("""
            SELECT author_id FROM authors WHERE author_name = %s;
        """, (author_name,))
        author_id_result = cursor.fetchone()

        if author_id_result is None:
            print("Author not found: " + author_name)
            # skip current poem if author not found
            return None

        author_id = author_id_result[0]

        # insert poem data into poems table
        cursor.execute("""
            INSERT INTO poems (author_id, poem_title, line_count) VALUES (%s, %s, %s)
            ON CONFLICT (poem_title) DO NOTHING
            RETURNING poem_id;
        """, (author_id, poem_title, line_count))
        poem_id_result = cursor.fetchone()

        if poem_id_result is None:
            # print("Poem already exists: " + poem_title)
            # skip current poem if failed to insert
            return None

        poem_id = poem_id_result[0]
        conn.commit()
        return poem_id

    except Exception as e:
        # exception occurred while inserting repeated poem
        print("Failed to insert poem: " + str(e))
        # rollback transaction if failed to insert
        conn.rollback()

    finally:
        cursor.close()
        conn.close()


# insert lines into PostgreSQL
def insert_lines(poem_id, lines):
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()

    if poem_id is None:
        return

    try:
        # line_number starts from 1, increment by 1 for each line
        for line_number, line_content in enumerate(lines, start=1):
            cursor.execute("""
                INSERT INTO lines (poem_id, line_number, line_content)
                VALUES (%s, %s, %s)
                ON CONFLICT (line_id) DO NOTHING;
            """, (poem_id, line_number, line_content))

        conn.commit()

    # print exception if failed to insert lines, avoid inserting process being interrupted
    except Exception as e:
        print("Failed to insert lines: " + str(e))
        conn.rollback()

    finally:
        cursor.close()
        conn.close()

# clean poem title
def clean_poem_title(title):
    # remove extra spaces
    title = ' '.join(title.split())
    # Remove all double quotes
    title = re.sub(r'"', '', title)
    # remove leading digits and dot
    title = re.sub(r'^\d+\.\s*', '', title)
    # remove leading and trailing quotes
    title = title.strip('"\'')
    # remove ending parenthesis temporarily, will recover later
    ending_parenthesis = re.search(r'\s*\([^()]*\)\s*$', title)
    if ending_parenthesis:
        title = title[:ending_parenthesis.start()].strip()
        ending = ending_parenthesis.group().strip()
    else:
        ending = ''
    # remove ending dash and spaces
    title = re.sub(r'\s*-\s*$', '', title)
    # remove ending non-alphanumeric characters
    title = re.sub(r'[^a-zA-Z0-9\s“‘”’]+$', '', title)
    # recover ending parenthesis
    if ending:
        title += ' ' + ending

    return title


# update poem titles in database
def update_poem_titles_in_db():
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()

    try:
        # get all poems titles
        cursor.execute("SELECT poem_id, poem_title FROM poems")
        poems = cursor.fetchall()

        # update poem titles
        for poem_id, original_title in poems:
            cleaned_title = clean_poem_title(original_title)
            # update if cleaned title is different from original title
            if cleaned_title != original_title:
                cursor.execute("""
                    UPDATE poems
                    SET poem_title = %s
                    WHERE poem_id = %s
                """, (cleaned_title, poem_id))

        conn.commit()

    except Exception as e:
        print("error in update_poem_titles_in_db" + str(e))
        conn.rollback()

    finally:
        cursor.close()
        conn.close()

import re

# clean poem line content
def clean_poem_line_content(line_content):
    # Remove all double quotes
    line_content = re.sub(r'"', '', line_content)
    # remove extra spaces at the beginning and end of the line
    line_content = line_content.strip()
    # remove non-alphanumeric characters at the beginning of the line
    line_content = re.sub(r'^[^a-zA-Z0-9]*', '', line_content)
    # remove non-alphanumeric characters at the end of the line
    line_content = re.sub(r'[^a-zA-Z0-9]*$', '', line_content)

    return line_content


# update poem lines in database
def update_poem_lines_in_db():
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()

    try:
        # get all lines
        cursor.execute("SELECT line_id, line_content FROM lines")
        lines = cursor.fetchall()

        # update lines
        for line_id, original_line_content in lines:
            cleaned_line_content = clean_poem_line_content(original_line_content)
            # update if cleaned title is different from original line content
            if cleaned_line_content != original_line_content:
                cursor.execute("""
                    UPDATE lines
                    SET line_content = %s
                    WHERE line_id = %s
                """, (cleaned_line_content, line_id))
            # remove line if line content is empty
            if not cleaned_line_content:
                cursor.execute("""
                    DELETE FROM lines
                    WHERE line_id = %s
                """, (line_id,))

        conn.commit()

    except Exception as e:
        print("error in update_poem_lines_in_db" + str(e) + str(line_id))
        conn.rollback()

    finally:
        cursor.close()
        conn.close()


# main function
def main():
    # step1: fetch and insert authors
    authors = get_authors()
    # print(authors)
    insert_authors(authors)
    print("Authors inserted successfully")

    # step2: fetch and insert poems
    titles = get_titles()
    # print(titles)
    for title in titles:
        poem_data = get_poem_by_title(title)
        if poem_data is None:
            continue
        # insert poem data into PostgreSQL
        poem = poem_data
        # if poem data is invalid, skip current poem
        if poem is None:
            continue
        poem_id = insert_poem(poem)
        insert_lines(poem_id, poem["lines"])

    print("Poems inserted successfully")
    update_poem_titles_in_db()
    print("Poem titles updated successfully")
    update_poem_lines_in_db()
    print("Poem lines updated successfully")


if __name__ == '__main__':
    main()
