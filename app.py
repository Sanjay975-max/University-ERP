
from flask import Flask, jsonify, request, render_template, redirect, session
import os
from werkzeug.security import check_password_hash
from database import get_db_connection

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "false").lower() == "true")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = os.environ.get("APP_USERNAME")
        password_hash = os.environ.get("APP_PASSWORD_HASH")

        if not username or not password_hash or not app.secret_key:
            error = "Login is not configured. Contact the administrator."
        elif request.form.get("username") == username and check_password_hash(
            password_hash, request.form.get("password", "")
        ):
            session["logged_in"] = True
            return redirect("/admin")
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.before_request
def require_login():
    if request.endpoint in ("login", "logout", "static"):
        return None
    if not session.get("logged_in"):
        return redirect("/login")


# 1. Home API
@app.route("/")
def home():
    return redirect("/admin")


# 2. View All Students (API)
@app.route("/students", methods=["GET"])
def get_students():

    conn = get_db_connection()

    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM STUDENT")
        students = cursor.fetchall()

        return jsonify(students)

    except Exception as err:
        return jsonify({"error": str(err)}), 500

    finally:
        cursor.close()
        conn.close()


# 3. Add New Student
@app.route("/add_student", methods=["POST"])
def add_student():

    data = request.get_json()

    if not data:
        return jsonify({"error": "Please provide student data"}), 400

    required_fields = [
        "admission_no", "name", "email", "phone",
        "gender", "date_of_birth", "admission_date",
        "department_id", "current_semester", "status"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    conn = get_db_connection()

    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()

    try:
        query = """
        INSERT INTO STUDENT
        (admission_no, name, email, phone, gender,
         date_of_birth, admission_date, department_id,
         current_semester, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            data["admission_no"],
            data["name"],
            data["email"],
            data["phone"],
            data["gender"],
            data["date_of_birth"],
            data["admission_date"],
            data["department_id"],
            data["current_semester"],
            data["status"]
        )

        cursor.execute(query, values)
        conn.commit()

        return jsonify({
            "message": "Student added successfully!",
            "student_id": cursor.lastrowid
        }), 201

    except Exception as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 400

    finally:
        cursor.close()
        conn.close()


# 4. Student Registration Page
@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html")


# 5. Admin Dashboard
@app.route("/admin")
def admin_dashboard():

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)

    try:
        # Student Statistics
        cursor.execute("SELECT COUNT(*) AS total FROM STUDENT")
        student_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM DEPARTMENT")
        department_count = cursor.fetchone()["total"]

        # Faculty Statistics
        cursor.execute("SELECT COUNT(*) AS total FROM faculty")
        faculty_count = cursor.fetchone()["total"]

        # Course Statistics
        cursor.execute("SELECT COUNT(*) AS total FROM course")
        course_count = cursor.fetchone()["total"]

        # Enrollment Statistics
        cursor.execute("SELECT COUNT(*) AS total FROM enrollment")
        enrollment_count = cursor.fetchone()["total"]

        # Fee Statistics
        cursor.execute("SELECT COUNT(*) AS total FROM fee_invoice")
        fee_count = cursor.fetchone()["total"]

        # Attendance Statistics
        cursor.execute("SELECT COUNT(*) AS total FROM attendance")
        attendance_count = cursor.fetchone()["total"]

        # Examination Statistics
        cursor.execute("SELECT COUNT(*) AS total FROM exam")
        exam_count = cursor.fetchone()["total"]

        # Result Statistics
        cursor.execute("SELECT COUNT(*) AS total FROM result")
        result_count = cursor.fetchone()["total"]

        # Scholarship Statistics
        cursor.execute("SELECT COUNT(*) AS total FROM scholarship")
        scholarship_count = cursor.fetchone()["total"]

        # Placement Statistics
        cursor.execute("SELECT COUNT(*) AS total FROM placement")
        placement_count = cursor.fetchone()["total"]

        return render_template(
            "admin.html",
            student_count=student_count,
            department_count=department_count,
            faculty_count=faculty_count,
            course_count=course_count,
            enrollment_count=enrollment_count,
            fee_count=fee_count,
            attendance_count=attendance_count,
            exam_count=exam_count,
            result_count=result_count,
            scholarship_count=scholarship_count,
            placement_count=placement_count
        )

    except Exception as err:
        return f"Dashboard Error: {err}", 500

    finally:
        cursor.close()
        conn.close()



# 6. Search and Manage Students
@app.route("/manage_students", methods=["GET"])
def manage_students():

    search = request.args.get("search", "")

    conn = get_db_connection()

    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        query = """
        SELECT * FROM STUDENT
        WHERE name LIKE %s OR admission_no LIKE %s
        ORDER BY student_id
        """

        search_value = f"%{search}%"

        cursor.execute(query, (search_value, search_value))
        students = cursor.fetchall()

        return render_template(
            "students.html",
            students=students,
            search=search
        )

    except Exception as err:
        return jsonify({"error": str(err)}), 500

    finally:
        cursor.close()
        conn.close()


# 7. Edit Student
@app.route("/edit_student/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):

    conn = get_db_connection()

    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == "POST":

            data = request.form

            query = """
            UPDATE STUDENT
            SET admission_no = %s,
                name = %s,
                email = %s,
                phone = %s,
                gender = %s,
                date_of_birth = %s,
                admission_date = %s,
                department_id = %s,
                current_semester = %s,
                status = %s
            WHERE student_id = %s
            """

            values = (
                data["admission_no"],
                data["name"],
                data["email"],
                data["phone"],
                data["gender"],
                data["date_of_birth"],
                data["admission_date"],
                data["department_id"],
                data["current_semester"],
                data["status"],
                student_id
            )

            cursor.execute(query, values)
            conn.commit()

            return redirect("/manage_students")

        cursor.execute(
            "SELECT * FROM STUDENT WHERE student_id = %s",
            (student_id,)
        )

        student = cursor.fetchone()

        if student is None:
            return "Student not found", 404

        return render_template(
            "edit_student.html",
            student=student
        )

    except Exception as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 400

    finally:
        cursor.close()
        conn.close()


# 8. Delete Student
@app.route("/delete_student/<int:student_id>", methods=["POST"])
def delete_student(student_id):

    conn = get_db_connection()

    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM STUDENT WHERE student_id = %s",
            (student_id,)
        )

        if cursor.rowcount == 0:
            return "Student not found", 404

        conn.commit()

        return redirect("/manage_students")

    except Exception as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 400

    finally:
        cursor.close()
        conn.close()


# 9. Display Add Department Page
@app.route("/add_department", methods=["GET"])
def add_department_page():
    return render_template("add_department.html")


# 10. Add Department to Database
@app.route("/add_department", methods=["POST"])
def add_department():

    department_name = request.form.get("department_name", "").strip()
    department_code = request.form.get("department_code", "").strip()
    office_location = request.form.get("office_location", "").strip() or None

    if not department_name or not department_code:
        return "Department name and code are required", 400

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor()

    try:
        query = """
        INSERT INTO DEPARTMENT
        (department_name, department_code, office_location)
        VALUES (%s, %s, %s)
        """

        values = (
            department_name,
            department_code,
            office_location
        )

        cursor.execute(query, values)
        conn.commit()

        return """
            <h2>Department Added Successfully!</h2>
            <a href="/add_department">Add Another Department</a><br><br>
            <a href="/manage_departments">View All Departments</a><br><br>
            <a href="/admin">Back to Dashboard</a>
        """

    except Exception as err:
        conn.rollback()
        return f"Error: {err}", 400

    finally:
        cursor.close()
        conn.close()


# 11. View All Departments
@app.route("/manage_departments", methods=["GET"])
def manage_departments():

    conn = get_db_connection()

    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT * FROM DEPARTMENT
            ORDER BY department_id
        """)

        departments = cursor.fetchall()

        return render_template(
            "departments.html",
            departments=departments
        )

    except Exception as err:
        return jsonify({"error": str(err)}), 500

    finally:
        cursor.close()
        conn.close()


# 12. Edit Department
@app.route("/edit_department/<int:department_id>", methods=["GET", "POST"])
def edit_department(department_id):

    conn = get_db_connection()

    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == "POST":

            data = request.form

            department_name = data.get("department_name", "").strip()
            department_code = data.get("department_code", "").strip()
            office_location = data.get("office_location", "").strip() or None

            if not department_name or not department_code:
                return "Department name and code are required", 400

            query = """
            UPDATE DEPARTMENT
            SET department_name = %s,
                department_code = %s,
                office_location = %s
            WHERE department_id = %s
            """

            values = (
                department_name,
                department_code,
                office_location,
                department_id
            )

            cursor.execute(query, values)

            if cursor.rowcount == 0:
                cursor.execute(
                    "SELECT department_id FROM DEPARTMENT WHERE department_id = %s",
                    (department_id,)
                )

                if cursor.fetchone() is None:
                    return "Department not found", 404

            conn.commit()

            return redirect("/manage_departments")

        cursor.execute(
            "SELECT * FROM DEPARTMENT WHERE department_id = %s",
            (department_id,)
        )

        department = cursor.fetchone()

        if department is None:
            return "Department not found", 404

        return render_template(
            "edit_department.html",
            department=department
        )

    except Exception as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 400

    finally:
        cursor.close()
        conn.close()


# 13. Delete Department
@app.route("/delete_department/<int:department_id>", methods=["POST"])
def delete_department(department_id):

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor()

    try:
        # Check whether students belong to this department
        cursor.execute(
            "SELECT COUNT(*) FROM STUDENT WHERE department_id = %s",
            (department_id,)
        )

        student_count = cursor.fetchone()[0]

        if student_count > 0:
            return "Cannot delete department. Students are assigned to it."

        # Delete department
        cursor.execute(
            "DELETE FROM DEPARTMENT WHERE department_id = %s",
            (department_id,)
        )

        if cursor.rowcount == 0:
            return "Department not found", 404

        conn.commit()

        return redirect("/manage_departments")

    except Exception as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 400

    finally:
        cursor.close()
        conn.close()



# 14. Manage Student Fees
@app.route("/manage_fees")
def manage_fees():

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)

    try:
        query = """
        SELECT
            fi.invoice_id,
            fi.student_id,
            s.name AS student_name,
            s.admission_no,
            fi.semester_id,
            sem.semester_number,
            fi.fee_type,
            fi.total_amount,
            COALESCE(SUM(p.amount_paid), 0) AS amount_paid,

            (fi.total_amount - COALESCE(SUM(p.amount_paid), 0))
            AS balance,

            fi.due_date,

            CASE
                WHEN COALESCE(SUM(p.amount_paid), 0) >= fi.total_amount
                    THEN 'Paid'
                WHEN COALESCE(SUM(p.amount_paid), 0) > 0
                    THEN 'Partial'
                ELSE 'Unpaid'
            END AS payment_status

        FROM fee_invoice fi

        JOIN STUDENT s
            ON fi.student_id = s.student_id

        JOIN semester sem
            ON fi.semester_id = sem.semester_id

        LEFT JOIN payment p
            ON fi.invoice_id = p.invoice_id

        GROUP BY
            fi.invoice_id,
            fi.student_id,
            s.name,
            s.admission_no,
            fi.semester_id,
            sem.semester_number,
            fi.fee_type,
            fi.total_amount,
            fi.due_date

        ORDER BY fi.invoice_id
        """

        cursor.execute(query)
        invoices = cursor.fetchall()

        return render_template(
            "fees.html",
            invoices=invoices
        )

    except Exception as err:
        return jsonify({"error": str(err)}), 500

    finally:
        cursor.close()
        conn.close()


# 15. Record Student Payment
@app.route("/record_payment", methods=["GET", "POST"])
def record_payment():

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)

    try:

        if request.method == "POST":

            invoice_id = request.form.get("invoice_id")
            amount_paid = request.form.get("amount_paid")
            payment_method = request.form.get("payment_method")
            transaction_id = request.form.get("transaction_id", "").strip() or None

            if not invoice_id or not amount_paid or not payment_method:
                return "Please fill all required fields", 400

            try:
                amount_paid = float(amount_paid)
            except ValueError:
                return "Invalid payment amount", 400

            if amount_paid <= 0:
                return "Payment amount must be greater than zero", 400

            # Check invoice and calculate current balance
            cursor.execute("""
                SELECT
                    fi.total_amount,
                    COALESCE(SUM(p.amount_paid), 0) AS amount_paid
                FROM fee_invoice fi
                LEFT JOIN payment p
                    ON fi.invoice_id = p.invoice_id
                WHERE fi.invoice_id = %s
                GROUP BY fi.invoice_id, fi.total_amount
            """, (invoice_id,))

            invoice = cursor.fetchone()

            if invoice is None:
                return "Invoice not found", 404

            balance = float(invoice["total_amount"]) - float(invoice["amount_paid"])

            if amount_paid > balance:
                return f"Payment exceeds remaining balance of Rs. {balance:.2f}", 400

            # Insert payment
            cursor.execute("""
                INSERT INTO payment
                (invoice_id, amount_paid, payment_method, transaction_id)
                VALUES (%s, %s, %s, %s)
            """, (
                invoice_id,
                amount_paid,
                payment_method,
                transaction_id
            ))

            # Calculate new balance and update invoice status
            new_paid = float(invoice["amount_paid"]) + amount_paid

            if new_paid >= float(invoice["total_amount"]):
                status = "Paid"
            elif new_paid > 0:
                status = "Partial"
            else:
                status = "Unpaid"

            cursor.execute("""
                UPDATE fee_invoice
                SET status = %s
                WHERE invoice_id = %s
            """, (status, invoice_id))

            conn.commit()

            return redirect("/manage_fees")

        # Load invoices for dropdown
        cursor.execute("""
            SELECT
                fi.invoice_id,
                fi.total_amount,
                s.name AS student_name,
                COALESCE(SUM(p.amount_paid), 0) AS amount_paid
            FROM fee_invoice fi
            JOIN STUDENT s
                ON fi.student_id = s.student_id
            LEFT JOIN payment p
                ON fi.invoice_id = p.invoice_id
            GROUP BY
                fi.invoice_id,
                fi.total_amount,
                s.name
            HAVING fi.total_amount > COALESCE(SUM(p.amount_paid), 0)
            ORDER BY fi.invoice_id
        """)

        invoices = cursor.fetchall()

        return render_template(
            "record_payment.html",
            invoices=invoices
        )

    except Exception as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 400

    finally:
        cursor.close()
        conn.close()


# 16. View Payment History
@app.route("/payment_history")
def payment_history():

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT
                p.payment_id,
                p.invoice_id,
                s.name AS student_name,
                s.admission_no,
                p.amount_paid,
                p.payment_date,
                p.payment_method,
                p.transaction_id
            FROM payment p
            JOIN fee_invoice fi
                ON p.invoice_id = fi.invoice_id
            JOIN STUDENT s
                ON fi.student_id = s.student_id
            ORDER BY p.payment_date DESC
        """

        cursor.execute(query)
        payments = cursor.fetchall()

        return render_template(
            "payment_history.html",
            payments=payments
        )

    except Exception as err:
        return jsonify({"error": str(err)}), 500

    finally:
        cursor.close()
        conn.close()


# 17. Fee Management Dashboard
@app.route("/fee_dashboard")
def fee_dashboard():

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT
                COUNT(*) AS total_invoices,
                COALESCE(SUM(total_amount), 0) AS total_fee,
                COALESCE(SUM(amount_paid), 0) AS total_collected,
                COALESCE(SUM(balance), 0) AS outstanding_balance,

                SUM(CASE
                    WHEN amount_paid >= total_amount THEN 1
                    ELSE 0
                END) AS paid_count,

                SUM(CASE
                    WHEN amount_paid > 0
                    AND amount_paid < total_amount THEN 1
                    ELSE 0
                END) AS partial_count,

                SUM(CASE
                    WHEN amount_paid = 0 THEN 1
                    ELSE 0
                END) AS unpaid_count

            FROM (
                SELECT
                    fi.invoice_id,
                    fi.total_amount,
                    COALESCE(SUM(p.amount_paid), 0) AS amount_paid,
                    fi.total_amount -
                    COALESCE(SUM(p.amount_paid), 0) AS balance

                FROM fee_invoice fi

                LEFT JOIN payment p
                    ON fi.invoice_id = p.invoice_id

                GROUP BY fi.invoice_id, fi.total_amount
            ) AS invoice_summary
        """

        cursor.execute(query)
        summary = cursor.fetchone()

        return render_template(
            "fee_dashboard.html",
            summary=summary
        )

    except Exception as err:
        return jsonify({"error": str(err)}), 500

    finally:
        cursor.close()
        conn.close()



# 18. Mark Student Attendance
@app.route("/mark_attendance", methods=["GET", "POST"])
def mark_attendance():

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)

    try:

        if request.method == "POST":

            offering_id = request.form.get("offering_id")
            attendance_date = request.form.get("attendance_date")

            if not offering_id or not attendance_date:
                return "Please select course and attendance date", 400

            # Get students enrolled in the selected course
            cursor.execute("""
                SELECT enrollment_id
                FROM enrollment
                WHERE offering_id = %s
            """, (offering_id,))

            students = cursor.fetchall()

            if not students:
                return "No students enrolled in this course", 404

            allowed_statuses = [
                "Present", "Absent", "Late", "Leave"
            ]

            # Save attendance for each student
            for student in students:

                enrollment_id = student["enrollment_id"]

                status = request.form.get(
                    f"status_{enrollment_id}"
                )

                if status not in allowed_statuses:
                    return "Invalid attendance status", 400

                cursor.execute("""
                    INSERT INTO attendance
                    (enrollment_id, attendance_date, attendance_status)
                    VALUES (%s, %s, %s)

                    ON DUPLICATE KEY UPDATE
                    attendance_status = VALUES(attendance_status)
                """, (
                    enrollment_id,
                    attendance_date,
                    status
                ))

            conn.commit()

            return redirect(
                f"/mark_attendance?offering_id={offering_id}"
                f"&attendance_date={attendance_date}"
            )

        # Load available courses and semesters
        cursor.execute("""
            SELECT
                co.offering_id,
                c.course_code,
                c.course_name,
                sem.semester_number,
                sem.academic_year,
                co.section

            FROM course_offering co

            JOIN course c
                ON co.course_id = c.course_id

            JOIN semester sem
                ON co.semester_id = sem.semester_id

            ORDER BY sem.semester_number, c.course_name
        """)

        offerings = cursor.fetchall()

        selected_offering_id = request.args.get("offering_id")
        attendance_date = request.args.get("attendance_date", "")

        students = []

        # Load students when a course is selected
        if selected_offering_id and attendance_date:

            cursor.execute("""
                SELECT
                    e.enrollment_id,
                    s.student_id,
                    s.name,
                    s.admission_no,
                    a.attendance_status

                FROM enrollment e

                JOIN STUDENT s
                    ON e.student_id = s.student_id

                LEFT JOIN attendance a
                    ON e.enrollment_id = a.enrollment_id
                    AND a.attendance_date = %s

                WHERE e.offering_id = %s

                ORDER BY s.name
            """, (
                attendance_date,
                selected_offering_id
            ))

            students = cursor.fetchall()

        return render_template(
            "mark_attendance.html",
            offerings=offerings,
            students=students,
            selected_offering_id=selected_offering_id,
            attendance_date=attendance_date
        )

    except Exception as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 400

    finally:
        cursor.close()
        conn.close()



# 19. Attendance Report
@app.route("/attendance_report")
def attendance_report():

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                student_id,
                name,
                total_classes,
                attended_classes,
                attendance_percentage
            FROM attendance_summary
            ORDER BY attendance_percentage ASC
        """)

        attendance_data = cursor.fetchall()

        return render_template(
            "attendance_report.html",
            attendance_data=attendance_data
        )

    except Exception as err:
        return jsonify({"error": str(err)}), 400

    finally:
        cursor.close()
        conn.close()


# 20. Add Examination
@app.route("/add_exam", methods=["GET", "POST"])
def add_exam():

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)

    try:

        if request.method == "POST":

            offering_id = request.form.get("offering_id")
            exam_name = request.form.get("exam_name")
            exam_type = request.form.get("exam_type")
            exam_date = request.form.get("exam_date")
            max_marks = request.form.get("max_marks")

            if not all([
                offering_id,
                exam_name,
                exam_type,
                max_marks
            ]):
                return "Please fill all required fields", 400

            if not exam_name.strip():
                return "Exam name cannot be empty", 400

            try:
                marks = float(max_marks)

                if marks <= 0 or marks > 9999.99:
                    return "Maximum marks must be between 0 and 9999.99", 400

            except ValueError:
                return "Invalid maximum marks", 400

            cursor.execute("""
                INSERT INTO exam
                (offering_id, exam_name, exam_type, exam_date, max_marks)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                offering_id,
                exam_name.strip(),
                exam_type,
                exam_date if exam_date else None,
                marks
            ))

            conn.commit()

            return redirect("/manage_exams")

        cursor.execute("""
            SELECT
                co.offering_id,
                c.course_code,
                c.course_name,
                sem.semester_number,
                sem.academic_year,
                co.section

            FROM course_offering co

            JOIN course c
                ON co.course_id = c.course_id

            JOIN semester sem
                ON co.semester_id = sem.semester_id

            ORDER BY c.course_name
        """)

        offerings = cursor.fetchall()

        return render_template(
            "add_exam.html",
            offerings=offerings
        )

    except Exception as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 400

    finally:
        cursor.close()
        conn.close()


# 21. Manage Examinations
@app.route("/manage_exams")
def manage_exams():

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                e.exam_id,
                e.exam_name,
                e.exam_type,
                e.exam_date,
                e.max_marks,
                c.course_code,
                c.course_name,
                sem.semester_number,
                sem.academic_year,
                co.section

            FROM exam e

            JOIN course_offering co
                ON e.offering_id = co.offering_id

            JOIN course c
                ON co.course_id = c.course_id

            JOIN semester sem
                ON co.semester_id = sem.semester_id

            ORDER BY e.exam_date DESC, e.exam_id DESC
        """)

        exams = cursor.fetchall()

        return render_template(
            "exams.html",
            exams=exams
        )

    except Exception as err:
        return jsonify({"error": str(err)}), 400

    finally:
        cursor.close()
        conn.close()



# 22. Edit Examination
@app.route("/edit_exam/<int:exam_id>", methods=["GET", "POST"])
def edit_exam(exam_id):

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)

    try:

        if request.method == "POST":

            offering_id = request.form.get("offering_id")
            exam_name = request.form.get("exam_name")
            exam_type = request.form.get("exam_type")
            exam_date = request.form.get("exam_date")
            max_marks = request.form.get("max_marks")

            if not all([
                offering_id,
                exam_name,
                exam_type,
                max_marks
            ]):
                return "Please fill all required fields", 400

            if not exam_name.strip():
                return "Exam name cannot be empty", 400

            try:
                marks = float(max_marks)

                if marks <= 0 or marks > 9999.99:
                    return "Invalid maximum marks", 400

            except ValueError:
                return "Invalid maximum marks", 400

            cursor.execute("""
                UPDATE exam
                SET offering_id = %s,
                    exam_name = %s,
                    exam_type = %s,
                    exam_date = %s,
                    max_marks = %s
                WHERE exam_id = %s
            """, (
                offering_id,
                exam_name.strip(),
                exam_type,
                exam_date if exam_date else None,
                marks,
                exam_id
            ))

            conn.commit()

            return redirect("/manage_exams")

        cursor.execute("""
            SELECT *
            FROM exam
            WHERE exam_id = %s
        """, (exam_id,))

        exam = cursor.fetchone()

        if not exam:
            return "Examination not found", 404

        cursor.execute("""
            SELECT
                co.offering_id,
                c.course_code,
                c.course_name,
                sem.semester_number,
                sem.academic_year,
                co.section
            FROM course_offering co
            JOIN course c ON co.course_id = c.course_id
            JOIN semester sem ON co.semester_id = sem.semester_id
            ORDER BY c.course_name
        """)

        offerings = cursor.fetchall()

        return render_template(
            "edit_exam.html",
            exam=exam,
            offerings=offerings
        )

    except Exception as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 400

    finally:
        cursor.close()
        conn.close()


# 23. Delete Examination
@app.route("/delete_exam/<int:exam_id>", methods=["POST"])
def delete_exam(exam_id):

    conn = get_db_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor()

    try:

        cursor.execute("""
            DELETE FROM exam
            WHERE exam_id = %s
        """, (exam_id,))

        if cursor.rowcount == 0:
            conn.rollback()
            return "Examination not found", 404

        conn.commit()

        return redirect("/manage_exams")

    except Exception as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 400

    finally:
        cursor.close()
        conn.close()



# ==========================================
# RESULT & GRADE MANAGEMENT
# ==========================================

def calculate_grade(marks, max_marks):
    percentage = (float(marks) / float(max_marks)) * 100

    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B+"
    elif percentage >= 60:
        return "B"
    elif percentage >= 50:
        return "C"
    elif percentage >= 40:
        return "D"
    else:
        return "F"


# 1. View All Results
@app.route("/manage_results")
def manage_results():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            r.result_id,
            r.exam_id,
            r.enrollment_id,
            r.marks_obtained,
            r.grade,
            e.exam_name,
            e.exam_type,
            e.max_marks,
            s.student_id,
            s.name AS student_name,
            s.admission_no,
            c.course_name,
            c.course_code
        FROM result r
        JOIN exam e ON r.exam_id = e.exam_id
        JOIN enrollment en ON r.enrollment_id = en.enrollment_id
        JOIN STUDENT s ON en.student_id = s.student_id
        JOIN course_offering co ON en.offering_id = co.offering_id
        JOIN course c ON co.course_id = c.course_id
        ORDER BY r.result_id DESC
    """)

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("results.html", results=results)


# 2. Add Result
@app.route("/add_result", methods=["GET", "POST"])
def add_result():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        exam_id = request.form.get("exam_id")
        enrollment_id = request.form.get("enrollment_id")
        marks = request.form.get("marks_obtained")

        try:
            marks = float(marks)

            cursor.execute("""
                SELECT max_marks
                FROM exam
                WHERE exam_id = %s
            """, (exam_id,))

            exam = cursor.fetchone()

            cursor.execute("""
                SELECT enrollment_id, offering_id
                FROM enrollment
                WHERE enrollment_id = %s
            """, (enrollment_id,))

            enrollment = cursor.fetchone()

            if not exam or not enrollment:
                raise ValueError("Invalid exam or enrollment.")

            if float(exam["max_marks"]) <= 0:
                raise ValueError("Maximum marks must be positive.")

            if marks < 0 or marks > float(exam["max_marks"]):
                raise ValueError(
                    "Marks must be between 0 and maximum marks."
                )

            cursor.execute("""
                SELECT offering_id
                FROM exam
                WHERE exam_id = %s
            """, (exam_id,))

            exam_offering = cursor.fetchone()

            if enrollment["offering_id"] != exam_offering["offering_id"]:
                raise ValueError(
                    "This student is not enrolled in the exam's course."
                )

            cursor.execute("""
                SELECT result_id
                FROM result
                WHERE exam_id = %s AND enrollment_id = %s
            """, (exam_id, enrollment_id))

            if cursor.fetchone():
                raise ValueError("Result already exists for this student and exam.")

            grade = calculate_grade(marks, exam["max_marks"])

            cursor.execute("""
                INSERT INTO result
                (exam_id, enrollment_id, marks_obtained, grade)
                VALUES (%s, %s, %s, %s)
            """, (exam_id, enrollment_id, marks, grade))

            conn.commit()

            cursor.close()
            conn.close()

            return redirect("/manage_results")

        except (ValueError, TypeError) as error:
            conn.rollback()
            error_message = str(error)

            cursor.execute("""
                SELECT exam_id, exam_name, max_marks, offering_id
                FROM exam
                ORDER BY exam_id
            """)
            exams = cursor.fetchall()

            cursor.execute("""
                SELECT en.enrollment_id, s.name, s.admission_no,
                       c.course_name, co.offering_id
                FROM enrollment en
                JOIN STUDENT s ON en.student_id = s.student_id
                JOIN course_offering co ON en.offering_id = co.offering_id
                JOIN course c ON co.course_id = c.course_id
                ORDER BY s.name
            """)
            enrollments = cursor.fetchall()

            cursor.close()
            conn.close()

            return render_template(
                "add_result.html",
                exams=exams,
                enrollments=enrollments,
                error=error_message
            )

    cursor.execute("""
        SELECT exam_id, exam_name, max_marks, offering_id
        FROM exam
        ORDER BY exam_id
    """)
    exams = cursor.fetchall()

    cursor.execute("""
        SELECT en.enrollment_id, s.name, s.admission_no,
               c.course_name, co.offering_id
        FROM enrollment en
        JOIN STUDENT s ON en.student_id = s.student_id
        JOIN course_offering co ON en.offering_id = co.offering_id
        JOIN course c ON co.course_id = c.course_id
        ORDER BY s.name
    """)
    enrollments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "add_result.html",
        exams=exams,
        enrollments=enrollments,
        error=None
    )


# 3. Edit Result
@app.route("/edit_result/<int:result_id>", methods=["GET", "POST"])
def edit_result(result_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        marks = request.form.get("marks_obtained")

        try:
            marks = float(marks)

            cursor.execute("""
                SELECT r.exam_id, e.max_marks
                FROM result r
                JOIN exam e ON r.exam_id = e.exam_id
                WHERE r.result_id = %s
            """, (result_id,))

            result = cursor.fetchone()

            if not result:
                cursor.close()
                conn.close()
                return "Result not found", 404

            if float(result["max_marks"]) <= 0:
                raise ValueError("Maximum marks must be positive.")

            if marks < 0 or marks > float(result["max_marks"]):
                raise ValueError("Marks exceed the allowed range.")

            grade = calculate_grade(marks, result["max_marks"])

            cursor.execute("""
                UPDATE result
                SET marks_obtained = %s, grade = %s
                WHERE result_id = %s
            """, (marks, grade, result_id))

            conn.commit()

            cursor.close()
            conn.close()

            return redirect("/manage_results")

        except (ValueError, TypeError) as error:
            conn.rollback()

            cursor.execute("""
                SELECT r.*, e.exam_name, e.max_marks,
                       s.name AS student_name
                FROM result r
                JOIN exam e ON r.exam_id = e.exam_id
                JOIN enrollment en ON r.enrollment_id = en.enrollment_id
                JOIN STUDENT s ON en.student_id = s.student_id
                WHERE r.result_id = %s
            """, (result_id,))

            result = cursor.fetchone()

            cursor.close()
            conn.close()

            if not result:
                return "Result not found", 404

            return render_template(
                "edit_result.html",
                result=result,
                error=str(error)
            )

    cursor.execute("""
        SELECT r.*, e.exam_name, e.max_marks,
               s.name AS student_name
        FROM result r
        JOIN exam e ON r.exam_id = e.exam_id
        JOIN enrollment en ON r.enrollment_id = en.enrollment_id
        JOIN STUDENT s ON en.student_id = s.student_id
        WHERE r.result_id = %s
    """, (result_id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if not result:
        return "Result not found", 404

    return render_template("edit_result.html", result=result, error=None)


# 4. Delete Result
@app.route("/delete_result/<int:result_id>", methods=["POST"])
def delete_result(result_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM result
        WHERE result_id = %s
    """, (result_id,))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/manage_results")


# ==========================================
# FACULTY MANAGEMENT
# ==========================================

# 1. View All Faculty
@app.route("/manage_faculty")
def manage_faculty():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            f.faculty_id,
            f.employee_no,
            f.name,
            f.email,
            f.phone,
            f.designation,
            f.joining_date,
            d.department_name
        FROM faculty f
        JOIN DEPARTMENT d
            ON f.department_id = d.department_id
        ORDER BY f.faculty_id
    """)

    faculty = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("faculty.html", faculty=faculty)


# 2. Add Faculty
@app.route("/add_faculty", methods=["GET", "POST"])
def add_faculty():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        employee_no = request.form.get("employee_no")
        name = request.form.get("name")
        email = request.form.get("email") or None
        phone = request.form.get("phone") or None
        designation = request.form.get("designation")
        department_id = request.form.get("department_id")
        joining_date = request.form.get("joining_date") or None

        if not employee_no or not name or not designation or not department_id:
            cursor.execute("SELECT * FROM DEPARTMENT")
            departments = cursor.fetchall()
            cursor.close()
            conn.close()

            return render_template(
                "add_faculty.html",
                departments=departments,
                error="Please fill all required fields."
            )

        cursor.execute("""
            INSERT INTO faculty
            (employee_no, name, email, phone, designation,
             department_id, joining_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            employee_no, name, email, phone, designation,
            department_id, joining_date
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/manage_faculty")

    cursor.execute("""
        SELECT department_id, department_name
        FROM DEPARTMENT
        ORDER BY department_name
    """)

    departments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "add_faculty.html",
        departments=departments,
        error=None
    )


# 3. Edit Faculty
@app.route("/edit_faculty/<int:faculty_id>", methods=["GET", "POST"])
def edit_faculty(faculty_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        employee_no = request.form.get("employee_no")
        name = request.form.get("name")
        email = request.form.get("email") or None
        phone = request.form.get("phone") or None
        designation = request.form.get("designation")
        department_id = request.form.get("department_id")
        joining_date = request.form.get("joining_date") or None

        cursor.execute("""
            UPDATE faculty
            SET employee_no = %s,
                name = %s,
                email = %s,
                phone = %s,
                designation = %s,
                department_id = %s,
                joining_date = %s
            WHERE faculty_id = %s
        """, (
            employee_no, name, email, phone, designation,
            department_id, joining_date, faculty_id
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/manage_faculty")

    cursor.execute("""
        SELECT *
        FROM faculty
        WHERE faculty_id = %s
    """, (faculty_id,))

    faculty_member = cursor.fetchone()

    if not faculty_member:
        cursor.close()
        conn.close()
        return "Faculty not found", 404

    cursor.execute("""
        SELECT department_id, department_name
        FROM DEPARTMENT
        ORDER BY department_name
    """)

    departments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "edit_faculty.html",
        faculty=faculty_member,
        departments=departments
    )


# 4. Delete Faculty
@app.route("/delete_faculty/<int:faculty_id>", methods=["POST"])
def delete_faculty(faculty_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check whether faculty is assigned to a course
    cursor.execute("""
        SELECT offering_id
        FROM course_offering
        WHERE faculty_id = %s
        LIMIT 1
    """, (faculty_id,))

    assignment = cursor.fetchone()

    if assignment:
        cursor.close()
        conn.close()
        return """
            <h2>Cannot Delete Faculty</h2>
            <p>This faculty member is assigned to a course offering.</p>
            <a href="/manage_faculty">Go Back</a>
        """, 400

    cursor.execute("""
        DELETE FROM faculty
        WHERE faculty_id = %s
    """, (faculty_id,))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/manage_faculty")



# ==========================================
# COURSE MANAGEMENT
# ==========================================

# 1. View All Courses
@app.route("/manage_courses")
def manage_courses():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            c.course_id,
            c.course_code,
            c.course_name,
            c.credits,
            c.description,
            d.department_name
        FROM course c
        JOIN DEPARTMENT d
            ON c.department_id = d.department_id
        ORDER BY c.course_id
    """)

    courses = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("courses.html", courses=courses)


# 2. Add New Course
@app.route("/add_course", methods=["GET", "POST"])
def add_course():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        course_code = request.form.get("course_code", "").strip()
        course_name = request.form.get("course_name", "").strip()
        department_id = request.form.get("department_id")
        credits = request.form.get("credits")
        description = request.form.get("description", "").strip() or None

        if not course_code or not course_name or not department_id or not credits:
            return "Please fill all required fields", 400

        try:
            credits = int(credits)

            if credits <= 0:
                return "Credits must be greater than zero", 400

            cursor.execute("""
                INSERT INTO course
                (course_code, course_name, department_id, credits, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                course_code,
                course_name,
                department_id,
                credits,
                description
            ))

            conn.commit()

            return redirect("/manage_courses")

        except Exception as err:
            conn.rollback()
            return f"Error: {err}", 400

        finally:
            cursor.close()
            conn.close()

    cursor.execute("""
        SELECT department_id, department_name
        FROM DEPARTMENT
        ORDER BY department_name
    """)

    departments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "add_course.html",
        departments=departments
    )


# 3. Edit Course
@app.route("/edit_course/<int:course_id>", methods=["GET", "POST"])
def edit_course(course_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        course_code = request.form.get("course_code", "").strip()
        course_name = request.form.get("course_name", "").strip()
        department_id = request.form.get("department_id")
        credits = request.form.get("credits")
        description = request.form.get("description", "").strip() or None

        if not course_code or not course_name or not department_id or not credits:
            return "Please fill all required fields", 400

        try:
            credits = int(credits)

            if credits <= 0:
                return "Credits must be greater than zero", 400

            cursor.execute("""
                UPDATE course
                SET course_code = %s,
                    course_name = %s,
                    department_id = %s,
                    credits = %s,
                    description = %s
                WHERE course_id = %s
            """, (
                course_code,
                course_name,
                department_id,
                credits,
                description,
                course_id
            ))

            conn.commit()

            return redirect("/manage_courses")

        except Exception as err:
            conn.rollback()
            return f"Error: {err}", 400

        finally:
            cursor.close()
            conn.close()

    cursor.execute("""
        SELECT *
        FROM course
        WHERE course_id = %s
    """, (course_id,))

    course = cursor.fetchone()

    if not course:
        cursor.close()
        conn.close()
        return "Course not found", 404

    cursor.execute("""
        SELECT department_id, department_name
        FROM DEPARTMENT
        ORDER BY department_name
    """)

    departments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "edit_course.html",
        course=course,
        departments=departments
    )


# 4. Delete Course Safely
@app.route("/delete_course/<int:course_id>", methods=["POST"])
def delete_course(course_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check whether course is assigned to any offering
        cursor.execute("""
            SELECT offering_id
            FROM course_offering
            WHERE course_id = %s
            LIMIT 1
        """, (course_id,))

        offering = cursor.fetchone()

        if offering:
            return """
                <h2>Cannot Delete Course</h2>
                <p>This course is assigned to a course offering.</p>
                <a href="/manage_courses">Go Back</a>
            """, 400

        cursor.execute("""
            DELETE FROM course
            WHERE course_id = %s
        """, (course_id,))

        if cursor.rowcount == 0:
            conn.rollback()
            return "Course not found", 404

        conn.commit()

        return redirect("/manage_courses")

    except Exception as err:
        conn.rollback()
        return f"Error: {err}", 400

    finally:
        cursor.close()
        conn.close()



# ==========================================
# ENROLLMENT MANAGEMENT
# ==========================================

# 1. View All Enrollments
@app.route("/manage_enrollments")
def manage_enrollments():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            e.enrollment_id,
            e.enrollment_date,
            e.status,
            s.student_id,
            s.admission_no,
            s.name AS student_name,
            c.course_code,
            c.course_name,
            sem.semester_number,
            sem.academic_year,
            co.section,
            f.name AS faculty_name
        FROM enrollment e
        JOIN STUDENT s ON e.student_id = s.student_id
        JOIN course_offering co ON e.offering_id = co.offering_id
        JOIN course c ON co.course_id = c.course_id
        JOIN semester sem ON co.semester_id = sem.semester_id
        JOIN faculty f ON co.faculty_id = f.faculty_id
        ORDER BY e.enrollment_id DESC
    """)

    enrollments = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "enrollments.html",
        enrollments=enrollments
    )


# 2. Add New Enrollment
@app.route("/add_enrollment", methods=["GET", "POST"])
def add_enrollment():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        student_id = request.form.get("student_id")
        offering_id = request.form.get("offering_id")
        enrollment_date = request.form.get("enrollment_date")
        status = request.form.get("status")

        if not student_id or not offering_id or not enrollment_date or not status:
            cursor.close()
            conn.close()
            return "Please fill all required fields", 400

        try:
            cursor.execute("""
                SELECT enrollment_id
                FROM enrollment
                WHERE student_id = %s AND offering_id = %s
            """, (student_id, offering_id))

            if cursor.fetchone():
                return "This student is already enrolled in this course offering.", 400

            cursor.execute("""
                INSERT INTO enrollment
                (student_id, offering_id, enrollment_date, status)
                VALUES (%s, %s, %s, %s)
            """, (student_id, offering_id, enrollment_date, status))

            conn.commit()

            return redirect("/manage_enrollments")

        except Exception as err:
            conn.rollback()
            return f"Error: {err}", 400

        finally:
            cursor.close()
            conn.close()

    cursor.execute("""
        SELECT student_id, admission_no, name
        FROM STUDENT
        ORDER BY name
    """)

    students = cursor.fetchall()

    cursor.execute("""
        SELECT
            co.offering_id,
            c.course_code,
            c.course_name,
            sem.semester_number,
            sem.academic_year,
            co.section,
            f.name AS faculty_name
        FROM course_offering co
        JOIN course c ON co.course_id = c.course_id
        JOIN semester sem ON co.semester_id = sem.semester_id
        JOIN faculty f ON co.faculty_id = f.faculty_id
        ORDER BY co.offering_id
    """)

    offerings = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "add_enrollment.html",
        students=students,
        offerings=offerings
    )


# 3. Edit Enrollment
@app.route("/edit_enrollment/<int:enrollment_id>", methods=["GET", "POST"])
def edit_enrollment(enrollment_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        student_id = request.form.get("student_id")
        offering_id = request.form.get("offering_id")
        enrollment_date = request.form.get("enrollment_date")
        status = request.form.get("status")

        if not student_id or not offering_id or not enrollment_date or not status:
            cursor.close()
            conn.close()
            return "Please fill all required fields", 400

        try:
            cursor.execute("""
                SELECT enrollment_id
                FROM enrollment
                WHERE student_id = %s
                AND offering_id = %s
                AND enrollment_id != %s
            """, (student_id, offering_id, enrollment_id))

            if cursor.fetchone():
                return "This student is already enrolled in this course offering.", 400

            cursor.execute("""
                UPDATE enrollment
                SET student_id = %s,
                    offering_id = %s,
                    enrollment_date = %s,
                    status = %s
                WHERE enrollment_id = %s
            """, (
                student_id,
                offering_id,
                enrollment_date,
                status,
                enrollment_id
            ))

            if cursor.rowcount == 0:
                cursor.rollback()
                return "Enrollment not found or no changes made.", 404

            conn.commit()

            return redirect("/manage_enrollments")

        except Exception as err:
            conn.rollback()
            return f"Error: {err}", 400

        finally:
            cursor.close()
            conn.close()

    cursor.execute("""
        SELECT *
        FROM enrollment
        WHERE enrollment_id = %s
    """, (enrollment_id,))

    enrollment = cursor.fetchone()

    if not enrollment:
        cursor.close()
        conn.close()
        return "Enrollment not found", 404

    cursor.execute("""
        SELECT student_id, admission_no, name
        FROM STUDENT
        ORDER BY name
    """)

    students = cursor.fetchall()

    cursor.execute("""
        SELECT
            co.offering_id,
            c.course_code,
            c.course_name,
            sem.semester_number,
            sem.academic_year,
            co.section,
            f.name AS faculty_name
        FROM course_offering co
        JOIN course c ON co.course_id = c.course_id
        JOIN semester sem ON co.semester_id = sem.semester_id
        JOIN faculty f ON co.faculty_id = f.faculty_id
        ORDER BY co.offering_id
    """)

    offerings = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "edit_enrollment.html",
        enrollment=enrollment,
        students=students,
        offerings=offerings
    )


# 4. Delete Enrollment Safely
@app.route("/delete_enrollment/<int:enrollment_id>", methods=["POST"])
def delete_enrollment(enrollment_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT attendance_id
            FROM attendance
            WHERE enrollment_id = %s
            LIMIT 1
        """, (enrollment_id,))

        if cursor.fetchone():
            return """
                <h2>Cannot Delete Enrollment</h2>
                <p>Attendance records are linked to this enrollment.</p>
                <a href="/manage_enrollments">Go Back</a>
            """, 400

        cursor.execute("""
            SELECT result_id
            FROM result
            WHERE enrollment_id = %s
            LIMIT 1
        """, (enrollment_id,))

        if cursor.fetchone():
            return """
                <h2>Cannot Delete Enrollment</h2>
                <p>Examination results are linked to this enrollment.</p>
                <a href="/manage_enrollments">Go Back</a>
            """, 400

        cursor.execute("""
            DELETE FROM enrollment
            WHERE enrollment_id = %s
        """, (enrollment_id,))

        if cursor.rowcount == 0:
            conn.rollback()
            return "Enrollment not found", 404

        conn.commit()

        return redirect("/manage_enrollments")

    except Exception as err:
        conn.rollback()
        return f"Error: {err}", 400

    finally:
        cursor.close()
        conn.close()



# ==========================================
# TIMETABLE MANAGEMENT
# ==========================================

# 1. View Complete Timetable
@app.route("/manage_timetable")
def manage_timetable():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            co.offering_id,
            c.course_code,
            c.course_name,
            sem.semester_number,
            sem.academic_year,
            f.name AS faculty_name,
            cl.room_number,
            cl.building,
            co.section,
            co.day_of_week,
            co.start_time,
            co.end_time
        FROM course_offering co
        JOIN course c ON co.course_id = c.course_id
        JOIN semester sem ON co.semester_id = sem.semester_id
        JOIN faculty f ON co.faculty_id = f.faculty_id
        LEFT JOIN classroom cl ON co.classroom_id = cl.classroom_id
        ORDER BY
            FIELD(co.day_of_week,
            'Monday', 'Tuesday', 'Wednesday',
            'Thursday', 'Friday', 'Saturday', 'Sunday'),
            co.start_time
    """)

    timetable = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "timetable.html",
        timetable=timetable
    )


# 2. Add New Class Schedule
@app.route("/add_timetable", methods=["GET", "POST"])
def add_timetable():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        course_id = request.form.get("course_id")
        semester_id = request.form.get("semester_id")
        faculty_id = request.form.get("faculty_id")
        classroom_id = request.form.get("classroom_id") or None
        section = request.form.get("section", "").strip() or "A"
        day_of_week = request.form.get("day_of_week")
        start_time = request.form.get("start_time") or None
        end_time = request.form.get("end_time") or None

        if not course_id or not semester_id or not faculty_id:
            cursor.close()
            conn.close()
            return "Please select course, semester and faculty.", 400

        if bool(start_time) != bool(end_time):
            cursor.close()
            conn.close()
            return "Please provide both start time and end time.", 400

        if start_time and end_time and start_time >= end_time:
            cursor.close()
            conn.close()
            return "End time must be later than start time.", 400

        try:
            cursor.execute("""
                INSERT INTO course_offering
                (course_id, semester_id, faculty_id,
                 classroom_id, section, day_of_week,
                 start_time, end_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                course_id,
                semester_id,
                faculty_id,
                classroom_id,
                section,
                day_of_week,
                start_time,
                end_time
            ))

            conn.commit()

            return redirect("/manage_timetable")

        except Exception as err:
            conn.rollback()
            return f"Error: {err}", 400

        finally:
            cursor.close()
            conn.close()

    cursor.execute("""
        SELECT course_id, course_code, course_name
        FROM course
        ORDER BY course_code
    """)
    courses = cursor.fetchall()

    cursor.execute("""
        SELECT semester_id, semester_number, academic_year
        FROM semester
        ORDER BY semester_id
    """)
    semesters = cursor.fetchall()

    cursor.execute("""
        SELECT faculty_id, employee_no, name
        FROM faculty
        ORDER BY name
    """)
    faculties = cursor.fetchall()

    cursor.execute("""
        SELECT classroom_id, room_number, building, room_type
        FROM classroom
        ORDER BY room_number
    """)
    classrooms = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "add_timetable.html",
        courses=courses,
        semesters=semesters,
        faculties=faculties,
        classrooms=classrooms
    )


# 3. Edit Class Schedule
@app.route("/edit_timetable/<int:offering_id>", methods=["GET", "POST"])
def edit_timetable(offering_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        course_id = request.form.get("course_id")
        semester_id = request.form.get("semester_id")
        faculty_id = request.form.get("faculty_id")
        classroom_id = request.form.get("classroom_id") or None
        section = request.form.get("section", "").strip() or "A"
        day_of_week = request.form.get("day_of_week")
        start_time = request.form.get("start_time") or None
        end_time = request.form.get("end_time") or None

        if not course_id or not semester_id or not faculty_id:
            cursor.close()
            conn.close()
            return "Please select course, semester and faculty.", 400

        if bool(start_time) != bool(end_time):
            cursor.close()
            conn.close()
            return "Please provide both start time and end time.", 400

        if start_time and end_time and start_time >= end_time:
            cursor.close()
            conn.close()
            return "End time must be later than start time.", 400

        try:
            cursor.execute("""
                UPDATE course_offering
                SET course_id = %s,
                    semester_id = %s,
                    faculty_id = %s,
                    classroom_id = %s,
                    section = %s,
                    day_of_week = %s,
                    start_time = %s,
                    end_time = %s
                WHERE offering_id = %s
            """, (
                course_id,
                semester_id,
                faculty_id,
                classroom_id,
                section,
                day_of_week,
                start_time,
                end_time,
                offering_id
            ))

            if cursor.rowcount == 0:
                cursor.rollback()
                return "Offering not found or no changes made.", 404

            conn.commit()

            return redirect("/manage_timetable")

        except Exception as err:
            conn.rollback()
            return f"Error: {err}", 400

        finally:
            cursor.close()
            conn.close()

    cursor.execute("""
        SELECT *
        FROM course_offering
        WHERE offering_id = %s
    """, (offering_id,))

    offering = cursor.fetchone()

    if not offering:
        cursor.close()
        conn.close()
        return "Timetable entry not found.", 404

    cursor.execute("""
        SELECT course_id, course_code, course_name
        FROM course
        ORDER BY course_code
    """)
    courses = cursor.fetchall()

    cursor.execute("""
        SELECT semester_id, semester_number, academic_year
        FROM semester
        ORDER BY semester_id
    """)
    semesters = cursor.fetchall()

    cursor.execute("""
        SELECT faculty_id, employee_no, name
        FROM faculty
        ORDER BY name
    """)
    faculties = cursor.fetchall()

    cursor.execute("""
        SELECT classroom_id, room_number, building, room_type
        FROM classroom
        ORDER BY room_number
    """)
    classrooms = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "edit_timetable.html",
        offering=offering,
        courses=courses,
        semesters=semesters,
        faculties=faculties,
        classrooms=classrooms
    )


# 4. Delete Class Schedule Safely
@app.route("/delete_timetable/<int:offering_id>", methods=["POST"])
def delete_timetable(offering_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT enrollment_id
            FROM enrollment
            WHERE offering_id = %s
            LIMIT 1
        """, (offering_id,))

        if cursor.fetchone():
            return """
                <h2>Cannot Delete Schedule</h2>
                <p>Students are enrolled in this course offering.</p>
                <a href="/manage_timetable">Go Back</a>
            """, 400

        cursor.execute("""
            SELECT exam_id
            FROM exam
            WHERE offering_id = %s
            LIMIT 1
        """, (offering_id,))

        if cursor.fetchone():
            return """
                <h2>Cannot Delete Schedule</h2>
                <p>Examinations are linked to this course offering.</p>
                <a href="/manage_timetable">Go Back</a>
            """, 400

        cursor.execute("""
            DELETE FROM course_offering
            WHERE offering_id = %s
        """, (offering_id,))

        if cursor.rowcount == 0:
            conn.rollback()
            return "Timetable entry not found.", 404

        conn.commit()

        return redirect("/manage_timetable")

    except Exception as err:
        conn.rollback()
        return f"Error: {err}", 400

    finally:
        cursor.close()
        conn.close()


# ================= SCHOLARSHIP MANAGEMENT =================

# 1. View All Scholarship Applications
@app.route("/manage_scholarships")
def manage_scholarships():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            sc.scholarship_id,
            st.name AS student_name,
            st.admission_no,
            sc.semester_id,
            sc.scholarship_name,
            sc.amount,
            sc.application_status
        FROM scholarship sc
        JOIN student st
        ON sc.student_id = st.student_id
        ORDER BY sc.scholarship_id DESC
    """)

    scholarships = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "scholarships.html",
        scholarships=scholarships
    )


# 2. Add Scholarship Application
@app.route("/add_scholarship", methods=["GET", "POST"])
def add_scholarship():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        student_id = request.form.get("student_id")
        semester_id = request.form.get("semester_id")
        scholarship_name = request.form.get("scholarship_name")
        amount = request.form.get("amount")

        try:
            if not student_id or not semester_id or not scholarship_name or not amount:
                return "Please fill all required fields."

            amount = float(amount)

            if amount <= 0:
                return "Scholarship amount must be greater than zero."

            cursor.execute("""
                INSERT INTO scholarship
                (student_id, semester_id, scholarship_name,
                 amount, application_status)
                VALUES (%s, %s, %s, %s, 'Pending')
            """, (
                student_id,
                semester_id,
                scholarship_name,
                amount
            ))

            conn.commit()

            cursor.close()
            conn.close()

            return redirect("/manage_scholarships")

        except Exception as e:
            conn.rollback()
            return f"Error adding scholarship: {e}"

    cursor.execute("""
        SELECT student_id, admission_no, name
        FROM student
        ORDER BY name
    """)
    students = cursor.fetchall()

    cursor.execute("""
        SELECT semester_id, semester_number, academic_year
        FROM semester
        ORDER BY semester_id
    """)
    semesters = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "add_scholarship.html",
        students=students,
        semesters=semesters
    )


# 3. Update Scholarship Application Status
@app.route("/update_scholarship_status/<int:scholarship_id>",
           methods=["POST"])
def update_scholarship_status(scholarship_id):

    status = request.form.get("application_status")

    allowed_statuses = [
        "Pending",
        "Approved",
        "Rejected",
        "Disbursed"
    ]

    if status not in allowed_statuses:
        return "Invalid scholarship status.", 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE scholarship
        SET application_status = %s
        WHERE scholarship_id = %s
    """, (status, scholarship_id))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/manage_scholarships")


# ================= PLACEMENT MANAGEMENT =================

# 1. View All Placement Records
@app.route("/manage_placements")
def manage_placements():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            p.placement_id,
            p.student_id,
            s.name AS student_name,
            s.admission_no,
            p.company_name,
            p.job_role,
            p.package_lpa,
            p.placement_date,
            p.placement_status
        FROM placement p
        JOIN student s
        ON p.student_id = s.student_id
        ORDER BY p.placement_id DESC
    """)

    placements = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "placements.html",
        placements=placements
    )


# 2. Add New Placement Record
@app.route("/add_placement", methods=["GET", "POST"])
def add_placement():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        student_id = request.form.get("student_id")
        company_name = request.form.get("company_name")
        job_role = request.form.get("job_role")
        package_lpa = request.form.get("package_lpa")
        placement_date = request.form.get("placement_date")
        placement_status = request.form.get("placement_status")

        try:
            if not student_id or not company_name:
                return "Student and company name are required."

            if package_lpa:
                package_lpa = float(package_lpa)

                if package_lpa <= 0:
                    return "Package must be greater than zero."

            cursor.execute("""
                INSERT INTO placement
                (student_id, company_name, job_role,
                 package_lpa, placement_date, placement_status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                student_id,
                company_name,
                job_role or None,
                package_lpa or None,
                placement_date or None,
                placement_status or "Applied"
            ))

            conn.commit()

            cursor.close()
            conn.close()

            return redirect("/manage_placements")

        except Exception as e:
            conn.rollback()
            return f"Error adding placement: {e}"

    cursor.execute("""
        SELECT student_id, admission_no, name
        FROM student
        ORDER BY name
    """)

    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "add_placement.html",
        students=students
    )


# 3. Update Placement Status
@app.route("/update_placement_status/<int:placement_id>",
           methods=["POST"])
def update_placement_status(placement_id):

    status = request.form.get("placement_status")

    allowed_statuses = [
        "Applied",
        "Shortlisted",
        "Interview",
        "Selected",
        "Joined",
        "Rejected"
    ]

    if status not in allowed_statuses:
        return "Invalid placement status.", 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE placement
        SET placement_status = %s
        WHERE placement_id = %s
    """, (status, placement_id))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/manage_placements")


# Run Flask Application
if __name__ == "__main__":
    app.run(debug=True)
