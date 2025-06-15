import uuid
import os
import pandas as pd
from sqlalchemy import create_engine, Column, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID

# --- Configuration ---
# Replace with your actual PostgreSQL connection string.
# Format: "postgresql://<user>:<password>@<host>:<port>/<dbname>"
DATABASE_URL = "postgresql://awikwok:wikwokthetok@localhost/essaydb"

# --- SQLAlchemy Setup ---
Base = declarative_base()

# --- Model Definitions ---
# The models are defined based on the ERD, with the requested modifications.

class Subject(Base):
    """
    Represents a subject, like 'IPA' or 'History'.
    """
    __tablename__ = 'subjects'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_name = Column(String(100), nullable=False, unique=True)
    
    def __repr__(self):
        return f"<Subject(id={self.id}, name='{self.subject_name}')>"

class Student(Base):
    """
    Represents a student.
    """
    __tablename__ = 'students'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.name}')>"

class Question(Base):
    """
    Represents a question for a specific subject.
    """
    __tablename__ = 'questions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_text = Column(Text, nullable=False, unique=True)
    preferred_answer = Column(Text, nullable=True)
    
    subject_id = Column(UUID(as_uuid=True), ForeignKey('subjects.id'), nullable=False)

    def __repr__(self):
        return f"<Question(id={self.id}, text='{self.question_text[:30]}...')>"

class TaskAnswer(Base):
    """
    Represents a student's answer to a specific question for a task.
    The 'ground_truth' column replaces 'answer_status'.
    """
    __tablename__ = 'task_answers'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    answer = Column(Text, nullable=False)
    status = Column(Boolean, nullable=True) # Changed from answer_status
    ground_truth = Column(Boolean, nullable=False) # Changed from answer_status

    # Foreign Keys
    subject_id = Column(UUID(as_uuid=True), ForeignKey('subjects.id'), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id'), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'), nullable=False)

    def __repr__(self):
        return f"<TaskAnswer(id={self.id}, student_id={self.student_id}, question_id={self.question_id})>"


# --- Seeding Logic ---

def seed_database_from_file(session, file_path, stats):
    """
    Populates the database with data from a given Excel file,
    handling merged cells for questions and reference answers.
    """
    print(f"Starting to seed database from {file_path}...")

    # --- 2. Read Data File ---
    try:
        df = pd.read_excel(file_path)

        # *** FIX: Use forward fill to handle merged cells in Excel ***
        df['Pertanyaan'] = df['Pertanyaan'].ffill()
        df['Jawaban Referensi'] = df['Jawaban Referensi'].ffill()

        # Drop any rows that *still* have no student or question after ffill
        df.dropna(subset=['Nama Siswa', 'Pertanyaan'], inplace=True)

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return
    except Exception as e:
        print(f"An error occurred while reading or processing the Excel file: {e}")
        return

    # --- 3. Get or Create Subject ---
    base_name = os.path.basename(file_path)
    subject_name = base_name.split(' ')[0]
    subject = session.query(Subject).filter_by(subject_name=subject_name).first()
    if not subject:
        subject = Subject(subject_name=subject_name)
        session.add(subject)
        session.commit()
        stats['subjects'] += 1
        print(f"Created subject: '{subject_name}'")
    else:
        print(f"Using existing subject: '{subject_name}'")


    # --- 4. Get or Create Students ---
    student_names = df['Nama Siswa'].unique()
    student_map = {s.name: s for s in session.query(Student).filter(Student.name.in_(student_names)).all()}
    
    new_student_names = set(student_names) - set(student_map.keys())
    if new_student_names:
        new_students = [Student(name=name) for name in new_student_names]
        session.add_all(new_students)
        session.commit()
        for student in new_students:
            student_map[student.name] = student
    
    stats['students']['new'] += len(new_student_names)
    stats['students']['existing'] += (len(student_names) - len(new_student_names))
    print(f"Students: {len(new_student_names)} new, {(len(student_names) - len(new_student_names))} existing.")
    
    # --- 5. Get or Create Questions ---
    questions_df = df.drop_duplicates(subset=['Pertanyaan'])
    question_texts = questions_df['Pertanyaan'].tolist()
    question_map = {q.question_text: q for q in session.query(Question).filter(Question.question_text.in_(question_texts)).all()}
    
    new_questions = []
    for _, row in questions_df.iterrows():
        if row['Pertanyaan'] not in question_map:
            new_q = Question(
                question_text=row['Pertanyaan'],
                preferred_answer=row['Jawaban Referensi'],
                subject_id=subject.id
            )
            new_questions.append(new_q)
            question_map[new_q.question_text] = new_q
            
    if new_questions:
        session.add_all(new_questions)
        session.commit()

    stats['questions']['new'] += len(new_questions)
    stats['questions']['existing'] += (len(question_texts) - len(new_questions))
    print(f"Questions: {len(new_questions)} new, {(len(question_texts) - len(new_questions))} existing.")


    # --- 6. Create Task Answers ---
    task_answers = []
    for _, row in df.iterrows():
        student = student_map[row['Nama Siswa']]
        question = question_map[row['Pertanyaan']]
        
        ground_truth_bool = str(row['True False']).upper() == 'TRUE'

        task_answer = TaskAnswer(
            student_id=student.id,
            question_id=question.id,
            subject_id=subject.id,
            answer=row['Jawaban Siswa'],
            ground_truth=ground_truth_bool
        )
        task_answers.append(task_answer)

    if task_answers:
        session.add_all(task_answers)
        session.commit()
    
    stats['task_answers'] += len(task_answers)
    print(f"Created {len(task_answers)} task answers.")

# --- Main Execution ---

if __name__ == "__main__":
    DATASET_DIR = "./dataset"
    engine = create_engine(DATABASE_URL)

    print("Checking database connection and creating tables if they don't exist...")
    Base.metadata.create_all(engine)
    print("Tables are ready.")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()

    stats = {
        'subjects': 0, 'students': {'new': 0, 'existing': 0},
        'questions': {'new': 0, 'existing': 0}, 'task_answers': 0
    }

    # IMPORTANT: This flag determines if the script clears the database before running.
    # Set to False if you want to add data without deleting existing records.
    CLEAR_DATABASE_ON_START = True

    try:
        if CLEAR_DATABASE_ON_START:
            print("CLEAR_DATABASE_ON_START is True. Deleting all existing data...")
            db_session.query(TaskAnswer).delete()
            db_session.query(Question).delete()
            db_session.query(Student).delete()
            db_session.query(Subject).delete()
            db_session.commit()
            print("All data cleared.")

        excel_files = [f for f in os.listdir(DATASET_DIR) if f.endswith('.xlsx')]
        if not excel_files:
            print(f"Warning: No Excel files (.xlsx) found in the '{DATASET_DIR}' directory.")
        else:
            print(f"Found {len(excel_files)} Excel files to process...")
            for excel_file in excel_files:
                file_path = os.path.join(DATASET_DIR, excel_file)
                print(f"\n--- Processing file: {excel_file} ---")
                try:
                    seed_database_from_file(db_session, file_path, stats)
                except Exception as e:
                    print(f"An unhandled error occurred while processing {excel_file}: {e}")
                    print("Rolling back changes for this file.")
                    db_session.rollback()
                    continue

        print("\n--- Seeding completed! ---")
        print("Final Statistics:")
        print(f"- Subjects created or used: {stats['subjects']}")
        print(f"- Students processed: {stats['students']['new']} new, {stats['students']['existing']} existing")
        print(f"- Questions processed: {stats['questions']['new']} new, {stats['questions']['existing']} existing")
        print(f"- Total Task Answers created: {stats['task_answers']}")
                
    except Exception as e:
        print(f"\nA critical error occurred during the main execution: {e}")
        db_session.rollback()
    finally:
        print("Closing database session.")
        db_session.close()

