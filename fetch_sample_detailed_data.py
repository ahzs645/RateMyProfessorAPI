import requests
import json
import base64
import time
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

# Take top 5 professors by rating count as examples
sample_professors = sorted(professors, key=lambda x: x.get("numRatings", 0), reverse=True)[:5]

print(f"Fetching detailed data for top 5 professors as examples...")
print("-" * 80)

# Function to fetch complete professor data
def fetch_professor_details(professor_graphql_id, professor_name):
    query = {
        "query": """
        query TeacherPage($id: ID!) {
            node(id: $id) {
                ... on Teacher {
                    id
                    legacyId
                    firstName
                    lastName
                    department
                    school {
                        name
                        city
                        state
                    }
                    # Course information
                    courseCodes {
                        courseName
                        courseCount
                    }
                    # Rating distribution
                    ratingsDistribution {
                        r1
                        r2
                        r3
                        r4
                        r5
                        total
                    }
                    # Professor tags
                    teacherRatingTags {
                        tagName
                        tagCount
                    }
                    # Recent ratings (first 20)
                    ratings(first: 20) {
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
                    }
                    # Overall stats
                    avgRating
                    avgDifficulty
                    numRatings
                    wouldTakeAgainPercent
                }
            }
        }
        """,
        "variables": {"id": professor_graphql_id}
    }
    
    try:
        response = requests.post("https://www.ratemyprofessors.com/graphql", json=query, headers=headers)
        data = response.json()
        return data.get("data", {}).get("node", {})
    except Exception as e:
        print(f"  Error fetching data for {professor_name}: {e}")
        return None

# Fetch detailed data for sample professors
detailed_professors = []

for prof in sample_professors:
    print(f"\nFetching data for: {prof['name']} ({prof.get('numRatings', 0)} ratings)")
    
    professor_graphql_id = prof.get("graphql_id")
    if not professor_graphql_id:
        continue
    
    details = fetch_professor_details(professor_graphql_id, prof['name'])
    
    if details:
        # Process the data
        enhanced_prof = {
            "name": f"{details.get('firstName', '')} {details.get('lastName', '')}".strip(),
            "id": details.get("legacyId"),
            "department": details.get("department"),
            "school": details.get("school", {}),
            "overall_rating": details.get("avgRating"),
            "difficulty": details.get("avgDifficulty"),
            "total_ratings": details.get("numRatings"),
            "would_take_again_percent": details.get("wouldTakeAgainPercent"),
            
            # Courses taught
            "courses": [
                {
                    "name": course.get("courseName"),
                    "review_count": course.get("courseCount")
                }
                for course in details.get("courseCodes", [])
            ],
            
            # Rating distribution
            "rating_distribution": {
                "5_stars": details.get("ratingsDistribution", {}).get("r5", 0),
                "4_stars": details.get("ratingsDistribution", {}).get("r4", 0),
                "3_stars": details.get("ratingsDistribution", {}).get("r3", 0),
                "2_stars": details.get("ratingsDistribution", {}).get("r2", 0),
                "1_star": details.get("ratingsDistribution", {}).get("r1", 0)
            },
            
            # Tags
            "tags": [
                {
                    "name": tag.get("tagName"),
                    "count": tag.get("tagCount")
                }
                for tag in details.get("teacherRatingTags", [])
            ],
            
            # Sample recent reviews
            "recent_reviews": []
        }
        
        # Process reviews
        for edge in details.get("ratings", {}).get("edges", []):
            review = edge.get("node", {})
            enhanced_prof["recent_reviews"].append({
                "date": review.get("date"),
                "course": review.get("class"),
                "quality_rating": review.get("helpfulRating"),
                "difficulty_rating": review.get("difficultyRating"),
                "comment": review.get("comment"),
                "grade_received": review.get("grade"),
                "tags": review.get("ratingTags", []),
                "online_class": review.get("isForOnlineClass"),
                "for_credit": review.get("isForCredit"),
                "attendance_mandatory": review.get("attendanceMandatory"),
                "would_take_again": review.get("wouldTakeAgain"),
                "textbook_required": review.get("textbookUse"),
                "helpful_count": review.get("thumbsUpTotal", 0),
                "not_helpful_count": review.get("thumbsDownTotal", 0)
            })
        
        detailed_professors.append(enhanced_prof)
        
        # Print summary
        print(f"  ✓ Courses: {len(enhanced_prof['courses'])}")
        print(f"  ✓ Tags: {', '.join([t['name'] for t in enhanced_prof['tags'][:5]])}")
        print(f"  ✓ Recent reviews: {len(enhanced_prof['recent_reviews'])}")
        
    time.sleep(1)  # Rate limiting

# Save the sample data
output_file = "sample_professors_detailed_data.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump({
        "description": "Sample detailed professor data from UNBC",
        "school_id": SCHOOL_ID,
        "fetch_date": datetime.now().isoformat(),
        "sample_size": len(detailed_professors),
        "professors": detailed_professors
    }, f, indent=2, ensure_ascii=False)

print(f"\n{'='*80}")
print(f"Sample data saved to: {output_file}")

# Show what additional data we can pull
print("\n📊 ADDITIONAL DATA AVAILABLE FOR ALL PROFESSORS:")
print("=" * 80)

if detailed_professors:
    prof = detailed_professors[0]
    
    print("\n1. COURSE INFORMATION:")
    for course in prof["courses"][:5]:
        print(f"   - {course['name']}: {course['review_count']} reviews")
    
    print("\n2. RATING DISTRIBUTION:")
    dist = prof["rating_distribution"]
    total = sum(dist.values())
    if total > 0:
        print(f"   5 stars: {dist['5_stars']} ({dist['5_stars']/total*100:.1f}%)")
        print(f"   4 stars: {dist['4_stars']} ({dist['4_stars']/total*100:.1f}%)")
        print(f"   3 stars: {dist['3_stars']} ({dist['3_stars']/total*100:.1f}%)")
        print(f"   2 stars: {dist['2_stars']} ({dist['2_stars']/total*100:.1f}%)")
        print(f"   1 star:  {dist['1_star']} ({dist['1_star']/total*100:.1f}%)")
    
    print("\n3. PROFESSOR TAGS:")
    for tag in prof["tags"][:10]:
        print(f"   - {tag['name']}: used {tag['count']} times")
    
    print("\n4. DETAILED REVIEW DATA:")
    if prof["recent_reviews"]:
        review = prof["recent_reviews"][0]
        print(f"   Sample review from {review['date']}:")
        print(f"   - Course: {review['course']}")
        print(f"   - Quality: {review['quality_rating']}/5, Difficulty: {review['difficulty_rating']}/5")
        print(f"   - Grade received: {review['grade_received']}")
        print(f"   - Online class: {review['online_class']}")
        print(f"   - Attendance mandatory: {review['attendance_mandatory']}")
        print(f"   - Would take again: {review['would_take_again']}")
        print(f"   - Tags: {', '.join(review['tags'])}")
        print(f"   - Helpful votes: {review['helpful_count']} 👍, {review['not_helpful_count']} 👎")
    
    print("\n5. ADDITIONAL DATA WE COULD FETCH:")
    print("   - Complete rating history (all reviews, not just recent)")
    print("   - Grade distribution analytics")
    print("   - Sentiment analysis of comments")
    print("   - Trending professors")
    print("   - Department comparisons")
    print("   - Historical rating trends over time")

print("\n💡 To fetch complete data for all 477 professors, run 'fetch_complete_professor_data.py'")
print("   (Note: This will take approximately 30-45 minutes due to rate limiting)")