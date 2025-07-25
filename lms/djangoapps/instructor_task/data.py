"""
Public data structures for the instructor_task app.
"""
from enum import Enum


class InstructorTaskTypes(str, Enum):
    """
    Enum describing the assortment of instructor tasks supported by edx-platform.
    """
    BULK_COURSE_EMAIL = "bulk_course_email"
    COHORT_STUDENTS = "cohort_students"
    COURSE_SURVEY_REPORT = "course_survey_report"
    DELETE_PROBLEM_STATE = "delete_problem_state"
    DETAILED_ENROLLMENT_REPORT = "detailed_enrollment_report"
    EXEC_SUMMARY_REPORT = "exec_summary_report"
    EXPORT_ORA2_DATA = "export_ora2_data"
    EXPORT_ORA2_SUBMISSION_FILES = "export_ora2_submission_files"
    EXPORT_ORA2_SUMMARY = "export_ora2_summary"
    GENERATE_ANONYMOUS_IDS_FOR_COURSE = "generate_anonymous_ids_for_course"
    GENERATE_CERTIFICATES_ALL_STUDENT = "generate_certificates_all_student"
    GENERATE_CERTIFICATES_CERTAIN_STUDENT = "generate_certificates_certain_student"
    GENERATE_CERTIFICATES_STUDENT_SET = "generate_certificates_student_set"
    GRADE_COURSE = "grade_course"
    GRADE_PROBLEMS = "grade_problems"
    MAY_ENROLL_INFO_CSV = "may_enroll_info_csv"
    INACTIVE_ENROLLED_STUDENTS_INFO_CSV = "inactive_enrolled_students_info_csv"
    OVERRIDE_PROBLEM_SCORE = "override_problem_score"
    PROBLEM_RESPONSES_CSV = "problem_responses_csv"
    PROCTORED_EXAM_RESULTS_REPORT = "proctored_exam_results_report"
    PROFILE_INFO_CSV = "profile_info_csv"
    REGENERATE_CERTIFICATES_ALL_STUDENT = "regenerate_certificates_all_student"
    RESCORE_PROBLEM = "rescore_problem"
    RESCORE_PROBLEM_IF_HIGHER = "rescore_problem_if_higher"
    RESET_PROBLEM_ATTEMPTS = "reset_problem_attempts"
