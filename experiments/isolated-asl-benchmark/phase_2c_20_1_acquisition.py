import urllib.request, json, os, zipfile, csv

sandbox_dir = r'd:\Singvox\Singvox\data\sandbox_continuous\how2sign_sample'
zip_url = 'https://huggingface.co/datasets/aipieces/How2Sign/resolve/main/val_rgb_front_clips/shard_001_018.zip'
zip_path = os.path.join(sandbox_dir, "shard_001_018.zip")

print("Downloading 82MB zip...")
if not os.path.exists(zip_path):
    data = urllib.request.urlopen(zip_url).read()
    with open(zip_path, 'wb') as f:
        f.write(data)
print("Finished download.")

print("Extracting videos...")
video_files = []
with zipfile.ZipFile(zip_path, 'r') as z:
    for name in z.namelist():
        if name.endswith('.mp4'):
            z.extract(name, sandbox_dir)
            video_files.append(name)
print(f"Extracted {len(video_files)} videos.")

if video_files:
    sample_video = video_files[0]
    sample_vid_id = os.path.splitext(os.path.basename(sample_video))[0].replace('-1-rgb_front', '')
    print(f"\nVerifying Sample ID: {sample_vid_id}")
    
    csv_path = os.path.join(sandbox_dir, 'how2sign_val.csv')
    found_match = False
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row['SENTENCE_NAME'] == os.path.splitext(os.path.basename(sample_video))[0]:
                print(f"Match found in CSV!")
                print(f"SENTENCE: {row['SENTENCE']}")
                print(f"START-END: {row['START']} - {row['END']}")
                found_match = True
                break
    
    if not found_match:
        print("Verification failed: Could not match video ID in CSV.")
    
    print("\nFile sizes:")
    print(f"Video {sample_video}: {os.path.getsize(os.path.join(sandbox_dir, sample_video))//1024} KB")
    print(f"Zip size: {os.path.getsize(zip_path)//(1024*1024)} MB")
