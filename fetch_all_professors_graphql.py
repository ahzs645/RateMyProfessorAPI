import requests
import json
import base64
import time

# Your school ID
SCHOOL_ID = 1448

# Headers from the API
headers = {
    "Authorization": "Basic dGVzdDp0ZXN0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    "Content-Type": "application/json",
    "Referer": f"https://www.ratemyprofessors.com/search/professors/{SCHOOL_ID}"
}

# GraphQL query to search professors at a specific school
search_query = {
    "query": """
    query TeacherSearchPaginationQuery($count: Int!, $cursor: String, $query: TeacherSearchQuery!) {
        search: newSearch {
            teachers(query: $query, first: $count, after: $cursor) {
                didFallback
                edges {
                    cursor
                    node {
                        id
                        legacyId
                        firstName
                        lastName
                        department
                        school {
                            name
                            id
                        }
                        avgRating
                        numRatings
                        avgDifficulty
                        wouldTakeAgainPercent
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    }
    """,
    "variables": {
        "count": 100,  # Max professors per request
        "query": {
            "text": "",  # Empty to get all
            "schoolID": base64.b64encode(f"School-{SCHOOL_ID}".encode()).decode()
        }
    }
}

all_professors = []
cursor = None
page = 1

print(f"Fetching professors from school ID {SCHOOL_ID}...")
print("-" * 50)

while True:
    # Update cursor for pagination
    if cursor:
        search_query["variables"]["cursor"] = cursor
    
    print(f"Fetching page {page}...")
    
    try:
        response = requests.post(
            "https://www.ratemyprofessors.com/graphql",
            json=search_query,
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            break
            
        data = response.json()
        
        # Extract professors from response
        teachers_data = data.get("data", {}).get("search", {}).get("teachers", {})
        edges = teachers_data.get("edges", [])
        
        if not edges:
            print("No more professors found.")
            break
            
        # Process each professor
        for edge in edges:
            professor = edge.get("node", {})
            if professor:
                prof_data = {
                    "id": professor.get("legacyId"),
                    "graphql_id": professor.get("id"),
                    "name": f"{professor.get('firstName', '')} {professor.get('lastName', '')}".strip(),
                    "firstName": professor.get("firstName"),
                    "lastName": professor.get("lastName"),
                    "department": professor.get("department"),
                    "school": professor.get("school", {}).get("name"),
                    "rating": professor.get("avgRating"),
                    "numRatings": professor.get("numRatings"),
                    "difficulty": professor.get("avgDifficulty"),
                    "wouldTakeAgainPercent": professor.get("wouldTakeAgainPercent")
                }
                all_professors.append(prof_data)
        
        print(f"  Found {len(edges)} professors on this page (Total: {len(all_professors)})")
        
        # Check if there's a next page
        page_info = teachers_data.get("pageInfo", {})
        if page_info.get("hasNextPage"):
            cursor = page_info.get("endCursor")
            page += 1
            time.sleep(1)  # Rate limiting
        else:
            print("No more pages.")
            break
            
    except Exception as e:
        print(f"Error: {str(e)}")
        break

# Sort by number of ratings
all_professors.sort(key=lambda x: x.get("numRatings", 0), reverse=True)

print("-" * 50)
print(f"\nTotal professors found: {len(all_professors)}")

# Save to JSON
if all_professors:
    output_file = f"professors_school_{SCHOOL_ID}_complete.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "school_id": SCHOOL_ID,
            "total_professors": len(all_professors),
            "fetch_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "professors": all_professors
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nData saved to: {output_file}")
    
    # Show statistics
    print("\nTop 10 professors by rating count:")
    print("-" * 80)
    print(f"{'Name':<30} {'Department':<25} {'Rating':<8} {'Ratings':<10} {'Difficulty':<10}")
    print("-" * 80)
    
    for prof in all_professors[:10]:
        name = prof["name"][:29]
        dept = (prof.get("department") or "N/A")[:24]
        rating = f"{prof.get('rating', 'N/A'):.1f}/5" if prof.get('rating') else "N/A"
        num_ratings = prof.get("numRatings", 0)
        difficulty = f"{prof.get('difficulty', 'N/A'):.1f}/5" if prof.get('difficulty') else "N/A"
        print(f"{name:<30} {dept:<25} {rating:<8} {num_ratings:<10} {difficulty:<10}")
    
    # Department breakdown
    departments = {}
    for prof in all_professors:
        dept = prof.get("department", "Unknown")
        if dept:
            departments[dept] = departments.get(dept, 0) + 1
    
    print(f"\n\nDepartments ({len(departments)} total):")
    sorted_depts = sorted(departments.items(), key=lambda x: x[1], reverse=True)
    for dept, count in sorted_depts[:15]:
        print(f"  {dept}: {count} professors")
else:
    print("\nNo professors found. This might mean:")
    print("  1. The school ID is incorrect")
    print("  2. The school has no rated professors")
    print("  3. There's an issue with the API")