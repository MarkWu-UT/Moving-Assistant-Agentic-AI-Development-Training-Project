import os
import re
import csv
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def extract_info_with_gpt(transcript, client):
    """
    Use OpenAI GPT to extract structured information from transcription text.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": "Extract moving-related information from this transcript. If information is not present, leave the field empty. For service_level, return: 'none', 'packing_only', 'unpacking_only', or 'both'. For lead_time, return the number of days."},
                {"role": "user", "content": f"Extract the following information from this moving-related transcript (return JSON format with these keys): \n\n"
                 f"company_name: Moving company mentioned\n"
                 f"origin_location: Where the person is moving from\n"
                 f"destination_location: Where the person is moving to\n"
                 f"price: Any quoted price or cost estimate\n"
                 f"lead_time: Number of days from pickup to delivery\n"
                 f"service_level: Whether packing/unpacking is offered ('none', 'packing_only', 'unpacking_only', 'both')\n"
                 f"insurance_coverage: Insurance options or coverage mentioned\n\n"
                 f"Transcript: {transcript}"}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        data = json.loads(response.choices[0].message.content)
        return data
    except Exception as e:
        print(f"Error extracting information with GPT: {str(e)}")
        return {
            "company_name": "",
            "origin_location": "",
            "destination_location": "",
            "price": "",
            "lead_time": "",
            "service_level": "none",
            "insurance_coverage": ""
        }

def extract_info_with_regex(transcript):
    """
    Use regex patterns to extract information as a fallback method.
    """
    data = {
        "company_name": "",
        "origin_location": "",
        "destination_location": "",
        "price": "",
        "lead_time": "",
        "service_level": "none",
        "insurance_coverage": ""
    }
    
    # Try to find locations (from X to Y)
    location_pattern = r"from\s+([A-Za-z\s]+)\s+to\s+([A-Za-z\s]+)"
    location_match = re.search(location_pattern, transcript)
    if location_match:
        data["origin_location"] = location_match.group(1).strip()
        data["destination_location"] = location_match.group(2).strip()
    
    # Try to find price information
    price_pattern = r"\$(\d+(?:,\d+)?(?:\.\d+)?)"
    price_match = re.search(price_pattern, transcript)
    if price_match:
        data["price"] = price_match.group(0)
    
    # Try to find lead time information
    lead_time_patterns = [
        r"(\d+)\s*(?:day|days|business\s*days?)",
        r"take(?:s)?\s*(?:about|around|approximately)?\s*(\d+)\s*(?:day|days|business\s*days?)",
        r"delivery\s*(?:in|within|takes?)?\s*(\d+)\s*(?:day|days|business\s*days?)"
    ]
    
    for pattern in lead_time_patterns:
        lead_time_match = re.search(pattern, transcript.lower())
        if lead_time_match:
            data["lead_time"] = lead_time_match.group(1)
            break
    
    # Check for packing and unpacking service mentions
    packing_pattern = r"pack(?:ing|ed)?\s+(?:service|included|available)"
    unpacking_pattern = r"unpack(?:ing|ed)?\s+(?:service|included|available)"
    has_packing = bool(re.search(packing_pattern, transcript.lower()))
    has_unpacking = bool(re.search(unpacking_pattern, transcript.lower()))
    
    # Determine service level
    if has_packing and has_unpacking:
        data["service_level"] = "both"
    elif has_packing:
        data["service_level"] = "packing_only"
    elif has_unpacking:
        data["service_level"] = "unpacking_only"
    else:
        data["service_level"] = "none"
    
    return data

def process_transcripts(directory):
    """
    Process all transcript text files in the directory and create a dataset.
    """
    # Get API key from environment variable
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Create a CSV file for the dataset
    output_file = os.path.join(directory, "moving_dataset.csv")
    
    # Fields for the CSV header in the desired order
    fields = ["file_name", "company_name", "origin_location", "destination_location", 
              "price", "lead_time", "service_level", "insurance_coverage", "raw_transcript"]
    
    # Data rows for the CSV
    data_rows = []
    
    # Process each text file in the directory
    for filename in os.listdir(directory):
        if filename.lower().endswith('.txt'):
            transcript_path = os.path.join(directory, filename)
            
            # Read the transcript
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript = f.read().strip()
            
            print(f"\nProcessing: {filename}")
            
            # First try to extract info with GPT
            try:
                data = extract_info_with_gpt(transcript, client)
            except Exception as e:
                print(f"Error with GPT extraction, falling back to regex: {str(e)}")
                # Fallback to regex extraction
                data = extract_info_with_regex(transcript)
            
            # Add to data rows
            data_rows.append({
                "file_name": filename,
                "company_name": data.get("company_name", ""),
                "origin_location": data.get("origin_location", ""),
                "destination_location": data.get("destination_location", ""),
                "price": data.get("price", ""),
                "lead_time": data.get("lead_time", ""),
                "service_level": data.get("service_level", "none"),
                "insurance_coverage": data.get("insurance_coverage", ""),
                "raw_transcript": transcript
            })
    
    # Write the data to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data_rows)
    
    print(f"\nDataset created: {output_file}")
    return output_file

if __name__ == "__main__":
    # Directory containing the transcription files
    transcripts_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_file = process_transcripts(transcripts_dir)
