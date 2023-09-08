from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3

customhost = "internshipdatabase.cpkr5ofaey5p.us-east-1.rds.amazonaws.com"
customuser = "admin"
custompass = "admin123"
customdb = "internshipDatabase"
custombucket = "hwt-internship"
customregion = "us-east-1"


app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'student' 

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('student.html')


@app.route("/addstud", methods=['POST'])
def AddStud():
    stud_id = request.form['stud_id']
    stud_name = request.form['stud_name']
    stud_image_file = request.files['stud_image_file']

    insert_sql = "INSERT INTO student VALUES (%s, %s)"
    cursor = db_conn.cursor()

    if stud_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (stud_id, stud_name))
        db_conn.commit()

        # Uplaod image file in S3 #
        stud_image_file_name_in_s3 = "stud-id-" + str(stud_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=stud_image_file_name_in_s3, Body=stud_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                stud_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddStudOutput.html', name=stud_name)



@app.route("/searchstud", methods=['POST'])
def GetStud():
    try:
        stud = request.form['search']

        # Corrected SQL statement with placeholder
        statement = "SELECT stud_id, stud_name FROM student WHERE stud_id = %s"
        cursor = db_conn.cursor()
        cursor.execute(statement, (stud,))
        
        # Fetch the result
        result = cursor.fetchone()

        if result:
            stud_id, stud_name = result
            return render_template('searchStudent.html', name=stud_name, id=stud_id)
        else:
            return render_template('searchError.html', id=stud)
        
    except Exception as e:
        return str(e)
        
    finally:
        cursor.close()


@app.route("/updatestud", methods=['POST'])
def UpStud():
    try:
        stud = request.form['update_id']
        name = request.form['update_name']

        # Corrected SQL statement with placeholder
        statement_get = "SELECT stud_name FROM student WHERE stud_id = %s"
        cursor = db_conn.cursor()
        cursor.execute(statement_get, (stud,))
        
        # Fetch the result
        result = cursor.fetchone()

        if result:

            stud_name = result[0]
            statement = "UPDATE student SET stud_name = %s WHERE stud_id = %s"
            cursor.execute(statement, (name, stud))
           
            return render_template('updateStudent.html', new=name, id=stud, old=stud_name)
        else:
            return render_template('updateError.html', id=stud)
        
    except Exception as e:
        return str(e)
        
    finally:
        cursor.close()


        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)



