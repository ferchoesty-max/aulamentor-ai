from src.repositories.mentor_repository import MentorRepository

users_repo = MentorRepository("users")
courses_repo = MentorRepository("courses")
enrollments_repo = MentorRepository("enrollments")
questions_repo = MentorRepository("questions")
attempts_repo = MentorRepository("attempts")
mastery_repo = MentorRepository("masteryProfiles")
recommendations_repo = MentorRepository("recommendations")