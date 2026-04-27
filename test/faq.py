import csv
import time
import requests
import urllib.parse

# CONFIG
INPUT_FILE = "hospital_chatbot_queries.csv"      # your input file
OUTPUT_FILE = "responses2.csv"    # output file
API_URL = "http://127.0.0.1:8000/chat?q="

# throttle: 20 questions per minute → 3 sec per request
DELAY = 5


def read_questions(file_path):
    questions = []
    with open(file_path, newline='', encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                questions.append(row[0].strip())
    return questions


def write_response(writer, question, response):
    writer.writerow([question, response])


def main():
    questions = read_questions(INPUT_FILE)

    with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["question", "response"])  # header

        for i, question in enumerate(questions):
            try:
                print(f"[{i+1}/{len(questions)}] Asking: {question}")

                # encode query properly
                encoded_q = urllib.parse.quote(question)
                url = API_URL + encoded_q

                res = requests.get(url, timeout=30)

                if res.status_code == 200:
                    data = res.json()
                    answer = data.get("response", "")
                else:
                    answer = f"ERROR: Status {res.status_code}"

            except Exception as e:
                answer = f"ERROR: {str(e)}"

            # write to CSV
            write_response(writer, question, answer)

            # flush immediately (important for long runs)
            f.flush()

            # throttle
            time.sleep(DELAY)

    print("✅ Done! Responses saved to responses.csv")


if __name__ == "__main__":
    main()