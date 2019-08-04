# Usage
```
python main.py [OPTIONS] image_file line_segmentation_file
Options:-
-b include border removal
-s include skew correction
-l include line merge

Example:-
python main.py -b -s -l sample.jpg line_seg.txt
```

Install the required libraries using `requirements.txt`

Input:-<br/>
Image File and Line Segmentation Text File

Output:-<br/>
Final Image File :- final.png <br/>
Final Segmentation File :- final_seg.txt
