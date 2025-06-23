psycnet_line = ",,,find|class|volume-wrapper~find_all|elem|li,True,find|elem|a,find|elem|a,,find_all|elem|span|1|2,swap,find|class|list,,5,True,D"
sagepub_line = ",,,find|class|loi__issues~find_all|class|loi__issue,True,find|elem|a,find|elem|a,,find|class|loi__issue__cover-date,,find|class|table-of-content,,,,D"

def assign_csv_line(journal_domain):
    if "psycnet" in journal_domain:
        return psycnet_line.split(",")
    elif "sagepub" in journal_domain:
        return sagepub_line.split(",")
