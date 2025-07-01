# File to keep lists of things that go wrong


no_pdf_found = []
no_pdf_text = []
no_comment_page = []
docs_looked_at = 0

title_reject_phrase = ["PrivateCitizen", "W-", "illegible", "anonymous"]
doc_titles_rejected = []

error_list_wrapper = []
error_list_wrapper.append(no_pdf_found)
error_list_wrapper.append(no_pdf_text)
error_list_wrapper.append(no_comment_page)

no_pdf_found_str = "No PDF found:"
no_pdf_text_str = "No PDF text:"
no_comment_page_str = "No comment page:"

error_list_string_wrapper = []
error_list_string_wrapper.append(no_pdf_found_str)
error_list_string_wrapper.append(no_pdf_text_str)
error_list_string_wrapper.append(no_comment_page_str)

#### DOCCCSS

docs_added = []
duplicate_files = []


docs_list_wrapper = []
docs_list_wrapper.append(docs_added)
docs_list_wrapper.append(duplicate_files)
docs_list_wrapper.append(doc_titles_rejected)

docs_added_str = "Docs added:"
duplicate_files_str = "Duplicate files:"
doc_titles_rejected_str = "Titles Rejected:"

docs_list_string_wrapper = []
docs_list_string_wrapper.append(docs_added_str)
docs_list_string_wrapper.append(duplicate_files_str)
docs_list_string_wrapper.append(doc_titles_rejected_str)