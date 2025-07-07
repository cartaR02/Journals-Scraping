# File to keep lists of things that go wrong


no_pdf_found = []
no_pdf_text = []
no_comment_page = []
database_insertion_error = []
duplication_checking_error = []
pdf_gathering_failure = []
docs_looked_at = 0

title_reject_phrase = ["PrivateCitizen", "W-", "illegible", "anonymous"]
doc_titles_rejected = []

error_list_wrapper = []
error_list_wrapper.append(no_pdf_found)
error_list_wrapper.append(no_pdf_text)
error_list_wrapper.append(no_comment_page)
error_list_wrapper.append(database_insertion_error)
error_list_wrapper.append(duplication_checking_error)
error_list_wrapper.append(pdf_gathering_failure)
error_list_wrapper.append(doc_titles_rejected)



no_pdf_found_str = "No PDF Found:"
no_pdf_text_str = "No PDF Text:"
no_comment_page_str = "No Comment Page:"
database_insertion_error_str = "Database Ensertion Error:"
duplication_checking_error_str = "Duplication Checking Error:"
pdf_gathering_failure_str = "Error Processing Comment For PDF:"
doc_titles_rejected_str = "Doc Titles Rejected:"

error_list_string_wrapper = []
error_list_string_wrapper.append(no_pdf_found_str)
error_list_string_wrapper.append(no_pdf_text_str)
error_list_string_wrapper.append(no_comment_page_str)
error_list_string_wrapper.append(database_insertion_error_str)
error_list_string_wrapper.append(pdf_gathering_failure_str)
error_list_string_wrapper.append(doc_titles_rejected_str)

#### DOCCCSS

docs_added = []
duplicate_files = []


docs_list_wrapper = []
docs_list_wrapper.append(docs_added)
docs_list_wrapper.append(duplicate_files)

docs_added_str = "Docs added:"
duplicate_files_str = "Duplicate files:"

docs_list_string_wrapper = []
docs_list_string_wrapper.append(docs_added_str)
docs_list_string_wrapper.append(duplicate_files_str)