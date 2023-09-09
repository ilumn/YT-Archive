```bash
python main.py --use-mongodb --processes 4
```
    --use-mongodb: Use MongoDB to track downloaded videos and cache comments.
    --processes 4: Define the number of simultaneous video downloads (default is 4, minimum 2, maximum 256).

Downloading Videos and Scraping Comments (Single-Processing)

```bash
python main.py --use-mongodb --single-processing
```
    --single-processing: Skip multiprocessing and download videos one at a time. 
                         More stable on sub-gigabit internet.