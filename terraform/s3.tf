/*resource "aws_s3_bucket" "tf_s3_bucket" {
  bucket = "html-bucket-younes"

  tags = {
    Name        = "html terraform bucket"
    Environment = "Dev"
  }
}

resource "aws_s3_object" "tf_s3_object" {
  bucket = aws_s3_bucket.tf_s3_bucket.bucket
  for_each = fileset() #creates a loop which returns all the files in the directory
  key    = "images/${each.value}" #appends the images folder to the file name
  source = "path/to/file"

}
*/