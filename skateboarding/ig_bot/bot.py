# /usr/bin/python3
import praw
import re
import os
import psycopg2
import pdb
import sys

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()
cur.execute("SELECT * from comment")
ids = [row[0] for row in cur]

reddit = praw.Reddit(client_id=os.environ['client_id'],
                     client_secret=os.environ['client_secret'],
                     user_agent=os.environ['user_agent'],
                     username=os.environ['reddit_username'],
                     password=os.environ['reddit_password'])


def compose_comment(handles):
    comment_compose = []
    for handle in handles:
        comment_compose.append(f'https://www.instagram.com/{handle}')
    if comment_compose:
        comment_compose.append("\n\nI am a bot.")
        comment_compose.append("If I am having problems")
        comment_compose.append("please send me a message")
        return ' '.join(comment_compose)


def submit_comment(comment_compose, this_id):
    if comment_compose is not None and this_id not in ids:
        submitted = False
        try:
            sys.stdout.write(f"{this_id}, {this_id.url}")
            sys.stdout.flush()
            this_id.reply(comment_compose)
            submitted = True
        except Exception as e:
            sys.stderr.write(f"failed to comment: {e}")
            sys.stderr.flush()

        if submitted:
            try:
                insert_id(this_id)
            except Exception as e:
                sys.stderr.write(f"failed to comment: {e}")
                sys.stderr.flush()
    else:
        sys.stdout.write(f"{this_id} has already been replied to")
        sys.stdout.flush()


def insert_id(id):
    cur.execute(f"INSERT INTO comment (id) VALUES ('{id}')")


def find_handles():
    for submission in reddit.subreddit(os.environ['subreddit']).new(limit=20):
        if '@' in submission.title:
            handles = re.findall(r'(?<=@)\w+', submission.title)
            if handles:
                submit_comment(compose_comment(handles), submission)

        for comment in submission.comments:
            if submission.author is not None and comment.author is not None:
                if submission.author.name in comment.author.name:
                    handles = re.findall(r'(?<=@)\w+', comment.body)
                    if handles:
                        submit_comment(compose_comment(handles), comment)


if __name__ == "__main__":
    find_handles()
    conn.commit()
    cur.close()
    conn.close()
