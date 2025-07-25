import requests
import json
import base64
import time
import os
from datetime import datetime

# Your school ID
SCHOOL_ID = 1448

# Headers from the API
headers = {
    "Authorization": "Basic dGVzdDp0ZXN0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    "Content-Type": "application/json"
}

# Load existing professor data
with open("professors_school_1448_complete.json", "r") as f:
    professor_data = json.load(f)
    professors = professor_data["professors"]

print(f"Found {len(professors)} professors to fetch detailed data for...")
print("-" * 80)

# Enhanced GraphQL query for professor details
professor_detail_query = {
    "query": """
    query TeacherRatingsPageQuery($id: ID!) {
        node(id: $id) {
            ... on Teacher {
                id
                legacyId
                firstName
                lastName
                department
                courseCodes {
                    courseName
                    courseCount
                }
                ratingsDistribution {
                    r1
                    r2
                    r3
                    r4
                    r5
                    total
                }
                teacherRatingTags {
                    tagName
                    tagCount
                }
                ratings(first: 100) {
                    edges {
                        node {
                            id
                            date
                            class
                            comment
                            helpfulRating
                            difficultyRating
                            isForOnlineClass
                            isForCredit
                            attendanceMandatory
                            wouldTakeAgain
                            grade
                            textbookUse
                            ratingTags
                            thumbsUpTotal
                            thumbsDownTotal
                        }
                    }
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
        }
    }
    """
}

# Function to fetch all ratings for a professor (with pagination)
def fetch_all_ratings(professor_graphql_id):
    all_ratings = []
    cursor = None
    
    while True:
        query = {
            "query": """
            query GetProfessorRatings($id: ID!, $cursor: String) {
                node(id: $id) {
                    ... on Teacher {
                        ratings(first: 100, after: $cursor) {
                            edges {
                                node {
                                    id
                                    date
                                    class
                                    comment
                                    helpfulRating
                                    difficultyRating
                                    isForOnlineClass
                                    isForCredit
                                    attendanceMandatory
                                    wouldTakeAgain
                                    grade
                                    textbookUse
                                    ratingTags
                                    thumbsUpTotal
                                    thumbsDownTotal
                                }
                            }
                            pageInfo {
                                hasNextPage
                                endCursor
                            }
                        }
                    }
                }
            }
            """,
            "variables": {
                "id": professor_graphql_id,
                "cursor": cursor
            }
        }
        
        try:
            response = requests.post("https://www.ratemyprofessors.com/graphql", json=query, headers=headers)
            data = response.json()
            
            ratings_data = data.get("data", {}).get("node", {}).get("ratings", {})
            edges = ratings_data.get("edges", [])
            
            for edge in edges:
                rating = edge.get("node", {})
                if rating:
                    all_ratings.append(rating)
            
            page_info = ratings_data.get("pageInfo", {})
            if page_info.get("hasNextPage"):
                cursor = page_info.get("endCursor")
                time.sleep(0.2)  # Rate limiting
            else:
                break
                
        except Exception as e:
            print(f"Error fetching ratings: {e}")
            break
    
    return all_ratings

# Fetch detailed data for each professor
enhanced_professors = []
batch_size = 10  # Process in batches to show progress

for i, prof in enumerate(professors):
    if i % batch_size == 0:
        print(f"\nProcessing professors {i+1}-{min(i+batch_size, len(professors))}...")
    
    professor_graphql_id = prof.get("graphql_id")
    if not professor_graphql_id:
        continue
    
    # Set up the query
    professor_detail_query["variables"] = {"id": professor_graphql_id}
    
    try:
        # Fetch professor details
        response = requests.post("https://www.ratemyprofessors.com/graphql", json=professor_detail_query, headers=headers)
        data = response.json()
        
        professor_info = data.get("data", {}).get("node", {})
        
        if professor_info:
            # Extract course codes
            courses = []
            for course in professor_info.get("courseCodes", []):
                courses.append({
                    "name": course.get("courseName"),
                    "count": course.get("courseCount")
                })
            
            # Extract rating tags
            tags = []
            for tag in professor_info.get("teacherRatingTags", []):
                tags.append({
                    "name": tag.get("tagName"),
                    "count": tag.get("tagCount")
                })
            
            # Get rating distribution
            dist = professor_info.get("ratingsDistribution", {})
            rating_distribution = {
                "5_stars": dist.get("r5", 0),
                "4_stars": dist.get("r4", 0),
                "3_stars": dist.get("r3", 0),
                "2_stars": dist.get("r2", 0),
                "1_star": dist.get("r1", 0),
                "total": dist.get("total", 0)
            }
            
            # Check if we need to fetch more ratings
            initial_ratings = professor_info.get("ratings", {})
            has_more = initial_ratings.get("pageInfo", {}).get("hasNextPage", False)
            
            # Get all ratings
            if has_more:
                print(f"  Fetching all ratings for {prof['name']} (has many ratings)...")
                all_ratings = fetch_all_ratings(professor_graphql_id)
            else:
                all_ratings = [edge["node"] for edge in initial_ratings.get("edges", [])]
            
            # Process ratings
            processed_ratings = []
            for rating in all_ratings:
                processed_ratings.append({
                    "date": rating.get("date"),
                    "class": rating.get("class"),
                    "comment": rating.get("comment"),
                    "quality": rating.get("helpfulRating"),
                    "difficulty": rating.get("difficultyRating"),
                    "online_class": rating.get("isForOnlineClass"),
                    "for_credit": rating.get("isForCredit"),
                    "attendance_mandatory": rating.get("attendanceMandatory"),
                    "would_take_again": rating.get("wouldTakeAgain"),
                    "grade": rating.get("grade"),
                    "textbook_use": rating.get("textbookUse"),
                    "tags": rating.get("ratingTags", []),
                    "thumbs_up": rating.get("thumbsUpTotal", 0),
                    "thumbs_down": rating.get("thumbsDownTotal", 0)
                })
            
            # Create enhanced professor object
            enhanced_prof = {
                **prof,  # Include all original data
                "courses": courses,
                "rating_tags": tags,
                "rating_distribution": rating_distribution,
                "total_ratings_fetched": len(processed_ratings),
                "ratings": processed_ratings
            }
            
            enhanced_professors.append(enhanced_prof)
            
            # Show progress
            if (i + 1) % 5 == 0:
                print(f"  Processed: {prof['name']} - {len(processed_ratings)} ratings, {len(courses)} courses, {len(tags)} tags")
        
        # Rate limiting
        time.sleep(0.5)
        
    except Exception as e:
        print(f"  Error processing {prof['name']}: {str(e)}")
        # Still add the professor with original data
        enhanced_professors.append(prof)

print("\n" + "-" * 80)
print(f"Successfully fetched detailed data for {len(enhanced_professors)} professors")

# Save enhanced data
output_file = f"professors_UNBC_complete_with_details_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump({
        "school_id": SCHOOL_ID,
        "school_name": "University of Northern British Columbia",
        "total_professors": len(enhanced_professors),
        "fetch_date": datetime.now().isoformat(),
        "professors": enhanced_professors
    }, f, indent=2, ensure_ascii=False)

print(f"\nEnhanced data saved to: {output_file}")

# Generate statistics
total_ratings = sum(prof.get("total_ratings_fetched", 0) for prof in enhanced_professors)
total_courses = sum(len(prof.get("courses", [])) for prof in enhanced_professors)
professors_with_tags = sum(1 for prof in enhanced_professors if prof.get("rating_tags"))

print("\nStatistics:")
print(f"  Total ratings collected: {total_ratings:,}")
print(f"  Total unique courses: {total_courses}")
print(f"  Professors with rating tags: {professors_with_tags}")

# Find most common tags
all_tags = {}
for prof in enhanced_professors:
    for tag in prof.get("rating_tags", []):
        tag_name = tag.get("name", "")
        tag_count = tag.get("count", 0)
        all_tags[tag_name] = all_tags.get(tag_name, 0) + tag_count

print("\nTop 20 Most Common Professor Tags:")
sorted_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:20]
for tag, count in sorted_tags:
    print(f"  {tag}: {count}")

# Find most reviewed courses
all_courses = {}
for prof in enhanced_professors:
    for course in prof.get("courses", []):
        course_name = course.get("name", "")
        course_count = course.get("count", 0)
        if course_name:
            all_courses[course_name] = all_courses.get(course_name, 0) + course_count

print("\nTop 20 Most Reviewed Courses:")
sorted_courses = sorted(all_courses.items(), key=lambda x: x[1], reverse=True)[:20]
for course, count in sorted_courses:
    print(f"  {course}: {count} reviews")

# Sample some interesting ratings
print("\nSample Recent Reviews:")
all_recent_ratings = []
for prof in enhanced_professors:
    for rating in prof.get("ratings", [])[:5]:  # Get first 5 from each
        if rating.get("comment") and rating.get("date"):
            all_recent_ratings.append({
                "professor": prof["name"],
                "date": rating["date"],
                "class": rating.get("class", "N/A"),
                "comment": rating["comment"][:150] + "..." if len(rating.get("comment", "")) > 150 else rating.get("comment", ""),
                "quality": rating.get("quality", "N/A"),
                "difficulty": rating.get("difficulty", "N/A")
            })

# Sort by date and show recent ones
all_recent_ratings.sort(key=lambda x: x["date"] if x["date"] else "", reverse=True)
for review in all_recent_ratings[:5]:
    print(f"\n  Professor: {review['professor']}")
    print(f"  Course: {review['class']}")
    print(f"  Date: {review['date']}")
    print(f"  Quality: {review['quality']}/5, Difficulty: {review['difficulty']}/5")
    print(f"  Comment: {review['comment']}")