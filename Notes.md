# Notes

## Handling Missing ISBNs in the Goodreads Dataset

### 1. What if a User-Rated ISBN is Not in the 20k Goodreads User Interaction Dataset?

If an ISBN rated by a user is not found in the 20k Goodreads user interaction dataset, it means that the dataset does not include interactions for that particular book. This could be due to several reasons:

- The book may be newly released or not widely covered in the dataset.
- The book may not have sufficient user ratings to be included in the dataset.
- There could be inconsistencies or errors in the data collection or integration process.

To address this, consider the following steps:
- **Check for Alternative Data Sources**: Look for other datasets or APIs that might include interactions for this ISBN.
- **Update the Dataset**: Periodically update the dataset with new interactions to ensure it reflects current user ratings.
- **Fallback Mechanisms**: Implement fallback strategies, such as recommending similar books based on other features if an ISBN is missing.

### 2. What if a Book Has a Title and Book ID but No ISBN?

If a book is listed with a title and a book ID but lacks an ISBN, it poses a challenge for identification and data integration. Possible solutions include:

- **Using Book ID for Retrieval**: If the book ID is unique within a system, use it to query other datasets or services to find the ISBN.
- **Metadata Enrichment**: Obtain additional metadata from other sources, such as library catalogs or book retailers, to fill in the missing ISBN.
- **Manual Verification**: In cases where automated methods fail, manually verify the book details to obtain the correct ISBN.

### 3. Distribution of ISBNS in the 20k Goodreads Dataset

Out of the 1.3 million unique ISBNs, it is important to determine how many are represented in the 20k Goodreads user interaction dataset. This involves:

- **Cross-Referencing ISBNS**: Compare the list of ISBNs in the 20k dataset with the total pool of 1.3 million ISBNs.
- **Calculating Coverage**: Compute the proportion of unique ISBNs from the total pool that are covered in the 20k dataset to understand its coverage and representativeness.
- **Analyzing Gaps**: Identify and analyze gaps where ISBNs from the larger pool are not represented in the dataset to understand potential limitations.


### LOOK TO SIMPLIFY THE DATASET
