
import sqlite3
import streamlit as st
import os
import pandas as pd
import random
import smtplib
import psycopg2

# Initialize SQLite database
MAIN_FOLDER = "Course"
DB_HOST = "tutorial-ugqr.onrender.com"  # e.g., "your-db-name.render.com"
DB_NAME = "test_databse_7lvq"
DB_USER = "root"
DB_PASSWORD = "ckhZrjUSVoewUk9tWIUj0GKMxZHFOHd4"
DB_PORT = "5432"  # Default PostgreSQL port

def get_db_connection():
    """Create a new database connection."""
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS User (
            U_ID SERIAL PRIMARY KEY,
            Name TEXT NOT NULL,
            Email_ID TEXT UNIQUE NOT NULL,
            Password TEXT NOT NULL,
            Course TEXT NOT NULL,  
            Status INTEGER,
            OTP INTEGER
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def fetch_all_users(status=None):
    conn = get_db_connection()
    if status is None:
        query = "SELECT U_ID, Name, Email_ID, Course FROM User"
        users = pd.read_sql_query(query, conn)
    else:
        query = "SELECT U_ID, Name, Email_ID, Course FROM User WHERE Status = ?"
        users = pd.read_sql_query(query, conn, params=(status,))
    conn.close()
    return users

def is_email_registered(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM User WHERE Email_ID = ?", (email,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def send_otp(email):
    otp = random.randint(100000, 999999)
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("scomcoaching@gmail.com", "xgbf hqum tlys gweq")  # Replace with your credentials

        subject = "Your Verification OTP"
        body = f"Your OTP for login is: {otp}"
        message = f"Subject: {subject}\n\n{body}"

        server.sendmail("scomcoaching@gmail.com", email, message)  # Replace with your credentials
        server.quit()
        return otp
    except Exception as e:
        st.error(f"Failed to send OTP: {e}")
        return None

def update_otp(email, otp):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE User SET OTP = ? WHERE Email_ID = ?", (otp, email))
    conn.commit()
    conn.close()

def verify_user(email, password, otp):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Password, OTP, Status FROM User WHERE Email_ID = ?", (email,))
    record = cursor.fetchone()
    conn.close()

    if record and record[0] == password and record[1] == otp and record[2] == 1:
        return True
    elif record and record[2] == 0:
        st.error("Account is inactive. Please contact support.")
    return False

def register_user(name, email, password, course):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO User (Name, Email_ID, Password, Course, Status) VALUES (?, ?, ?, ?, 0)",
                       (name, email, password, course))
        conn.commit()
        st.success("User  registered successfully! Your account is pending activation.")
    except sqlite3.IntegrityError:
        st.error("Email already exists. Please try a different email.")
    conn.close()

def fetch_user(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Name, Email_ID, Password, Course FROM User WHERE Email_ID = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def login_page():
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user:
        if st.session_state.user["role"] == "Admin":
            st.success("Welcome, Admin!")
            admin_page()
        else:
            user_page()
    else:
        choice = st.sidebar.selectbox("Choose an option", ["Login", "Register"])

        if choice == "Register":
            st.subheader("User  Registration")
            name = st.text_input("Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            main_folder = MAIN_FOLDER
            courses = list_folders(main_folder)

            if courses:
                course = st.selectbox("Select a Course", courses)
            else:
                st.error("No courses available.")
                course = None

            if st.button("Register"):
                if name and email and password and course:
                    register_user(name, email, password, course)
                else:
                    st.error("All fields are required.")

        elif choice == "Login":
            st.subheader("Login")
            email = st.text_input("Email", placeholder="Enter Your Email ID")
            password = st.text_input("Password", placeholder="Enter Your Password", type="password")
            if email == "admin@gmail.com" and password == "123":
                st.session_state.user = {
                    "role": "Admin",
                    "name": "Admin",
                    "email": email,
                }
                st.success("Welcome, Admin!")
                st.rerun()

            if st.button("Login"):
                if is_email_registered(email):
                    user = fetch_user(email)
                    if user:
                        stored_password = user[2]
                        status = fetch_user_status(email)

                        if stored_password == password and status == 1:
                            otp = send_otp(email)
                            if otp:
                                update_otp(email, otp)
                                st.session_state.email = email
                                st.session_state.password = password
                                st.session_state.otp_sent = True
                                st.session_state.otp_verified = False
                                st.session_state.otp = otp
                                st.session_state.page = "otp_verification"  # Set the page to OTP verification
                                st.rerun()  # Rerun to navigate to the new page
                        elif status == 0:
                            st.error("Account is inactive. Please contact support.")
                        else:
                            st.error("Invalid password.")
                    else:
                        st.error("Failed to fetch user details.")
                else:
                    st.error("Email not registered. Please register first.")

def otp_verification_page():
    st.subheader("OTP Verification")
    entered_otp = st.text_input("Enter OTP", type="password")

    if st.button("Verify OTP"):
        if entered_otp:
            if entered_otp == str(st.session_state.otp):
                st.success("OTP verified successfully!")
                user = fetch_user(st.session_state.email)
                if user:
                    st.session_state.user = {
                        "role": "User ",
                        "name": user[0],
                        "email": user[1],
                        "password": user[2],
                        "course": user[3],
                    }
                    st.session_state.otp_verified = True
                    st.session_state.page = "user"  # Set the page to user page
                    st.rerun()  # Rerun to navigate to the new page
                else:
                    st.error("Failed to fetch user details.")
            else:
                st.error("Invalid OTP. Please try again.")
        else:
            st.error("Please enter the OTP.")

def fetch_user_status(email):
     conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Status FROM User WHERE Email_ID = ?", (email,))
    status = cursor.fetchone()
    conn.close()
    return status[0] if status else None

def list_folders(main_folder):
    try:
        return [folder for folder in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder, folder))]
    except FileNotFoundError:
        st.error(f"The folder '{main_folder}' does not exist.")
        return []

def fetch_all_users(status=None):
     conn = get_db_connection()
    if status is None:
        # Fetch all users if no status filter is applied
        query = "SELECT U_ID, Name, Email_ID, Course, Status FROM User"
        users = pd.read_sql_query(query, conn)
    else:
        # Fetch users with specific status
        query = "SELECT U_ID, Name, Email_ID, Course, Status FROM User WHERE Status = ?"
        users = pd.read_sql_query(query, conn, params=(status,))
    conn.close()
    return users
    
def fetch_user_status(email):
     conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Status FROM User WHERE Email_ID = ?", (email,))
    status = cursor.fetchone()
    conn.close()
    return status[0] if status else None

def list_folders(main_folder):
    try:
        return [folder for folder in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder, folder))]
    except FileNotFoundError:
        st.error(f"The folder '{main_folder}' does not exist.")
        return []


def admin_page(): 
    if st.sidebar.button("Logout"):
        st.session_state.user = None  # Clear user session  
        st.success("You have been logged out successfully!")
        st.rerun()


    main_folder = MAIN_FOLDER  # Shared folder path

    admin_option = st.sidebar.selectbox(
    "Choose an action:",
    ["Manage Files", "Manage Users", "Manage Courses"])
    #course_action = st.sidebar.selectbox("Manage Course:", ["Add New Course", "View Courses", "Edit Courses", "Delete Courses"])

    if admin_option == "Manage Files":
        file_action = st.sidebar.selectbox("Manage files:", ["Upload Files","Delete Files","Add Folders","Delete Folders"])
        if file_action == "Upload Files":
            st.subheader("Upload Program Files")

            # Select a program folder
            program_folders = list_folders(main_folder)
            if program_folders:
                selected_program_folder = st.selectbox("Select a program folder:", program_folders)
                if selected_program_folder:
                    program_folder_path = os.path.join(main_folder, selected_program_folder)

                    # Check for Modules
                    primary_subfolders = list_folders(program_folder_path)
                    if primary_subfolders:
                        selected_primary_subfolder = st.selectbox("Select a Module to upload files:", primary_subfolders)
                        primary_subfolder_path = os.path.join(program_folder_path, selected_primary_subfolder)

                        # Check for Topics
                        secondary_subfolders = list_folders(primary_subfolder_path)
                        if secondary_subfolders:
                            selected_secondary_subfolder = st.selectbox("Select a Topic to upload files:", secondary_subfolders)
                            secondary_subfolder_path = os.path.join(primary_subfolder_path, selected_secondary_subfolder)

                            # Upload files to the Topic
                            uploaded_files = st.file_uploader(
                                "Upload files to the selected Topic:",
                                type=None,  # Allow all file types
                                accept_multiple_files=True
                            )
                            if uploaded_files:
                                for uploaded_file in uploaded_files:
                                    save_file_to_folder(uploaded_file, secondary_subfolder_path)
                                st.success(f"Files uploaded successfully to '{selected_secondary_subfolder}'.")
                        else:
                            st.info(f"No Topics found in '{selected_primary_subfolder}'. Uploading files to the Module.")

                            # Upload files to the Module
                            uploaded_files = st.file_uploader(
                                "Upload files to the selected Module:",
                                type=None,  # Allow all file types
                                accept_multiple_files=True
                            )
                            if uploaded_files:
                                for uploaded_file in uploaded_files:
                                    save_file_to_folder(uploaded_file, primary_subfolder_path)
                                st.success(f"Files uploaded successfully to '{selected_primary_subfolder}'.")
                    else:
                        st.info(f"No Modules found in '{selected_program_folder}'. Uploading files to the program folder.")

                        # Upload files to the program folder
                        uploaded_files = st.file_uploader(
                            "Upload files to the selected program folder:",
                            type=None,  # Allow all file types
                            accept_multiple_files=True
                        )
                        if uploaded_files:
                            for uploaded_file in uploaded_files:
                                save_file_to_folder(uploaded_file, program_folder_path)
                            st.success(f"Files uploaded successfully to '{selected_program_folder}'.")
            else:
                st.info(f"No program folders found in '{main_folder}'. Add program folders first.")


        elif file_action == "Add Folders":
            st.subheader("Add New Subfolder")

            # Select a program folder
            program_folders = list_folders(main_folder)
            if program_folders:
                selected_program_folder = st.selectbox("Select a program folder:", program_folders)
                if selected_program_folder:
                    program_folder_path = os.path.join(main_folder, selected_program_folder)

                    # Option to create a Module
                    st.write("### Create Module")
                    primary_subfolder_name = st.text_input("Enter the name of the Module:")
                    if st.button("Create Module"):
                        if primary_subfolder_name.strip():
                            create_subfolder(program_folder_path, primary_subfolder_name.strip())
                            st.success(f"Module '{primary_subfolder_name}' created successfully in '{selected_program_folder}'.")
                        else:
                            st.warning("Please enter a valid name for the Module.")

                    # Option to create a Topic
                    st.write("### Create Topic")
                    subfolders = list_folders(program_folder_path)
                    if subfolders:
                        selected_subfolder = st.selectbox("Select a Module to add a Topic:", subfolders)
                        if selected_subfolder:
                            subfolder_path = os.path.join(program_folder_path, selected_subfolder)

                            secondary_subfolder_name = st.text_input("Enter the name of the Topic:")
                            if st.button("Create Topic"):
                                if secondary_subfolder_name.strip():
                                    create_subfolder(subfolder_path, secondary_subfolder_name.strip())
                                    st.success(f"Topic '{secondary_subfolder_name}' created successfully in '{selected_subfolder}'.")
                                else:
                                    st.warning("Please enter a valid name for the Topic.")
                    else:
                        st.info(f"No Modules found in '{selected_program_folder}'. Create a Module first.")
            else:
                st.info(f"No program folders found in '{main_folder}'. Add program folders first.")


        elif file_action == "Delete Files":
            st.subheader("Delete Uploaded Files")

            # Select a program folder
            program_folders = list_folders(main_folder)
            if program_folders:
                selected_program_folder = st.selectbox("Select a program folder:", program_folders)
                if selected_program_folder:
                    program_folder_path = os.path.join(main_folder, selected_program_folder)

                    # Check for Modules
                    primary_subfolders = list_folders(program_folder_path)
                    if primary_subfolders:
                        selected_primary_subfolder = st.selectbox("Select a Module:", primary_subfolders)
                        primary_subfolder_path = os.path.join(program_folder_path, selected_primary_subfolder)

                        # Check for Topics
                        secondary_subfolders = list_folders(primary_subfolder_path)
                        if secondary_subfolders:
                            selected_secondary_subfolder = st.selectbox("Select a Topic:", secondary_subfolders)
                            secondary_subfolder_path = os.path.join(primary_subfolder_path, selected_secondary_subfolder)

                            # List files in the Topic
                            files = list_files(secondary_subfolder_path)
                            if files:
                                selected_file = st.selectbox("Select a file to delete:", files)
                                if st.button("Delete File from Secondary Folder"):
                                    delete_file(secondary_subfolder_path, selected_file)
                            else:
                                st.info("No files found in the selected Topic.")
                        else:
                            st.info(f"No Topics found in '{selected_primary_subfolder}'. Deleting files from the Module.")

                            # List files in the Module
                            files = list_files(primary_subfolder_path)
                            if files:
                                selected_file = st.selectbox("Select a file to delete:", files)
                                if st.button("Delete File from Primary Folder"):
                                    delete_file(primary_subfolder_path, selected_file)
                                    st.success(f"File '{selected_file}' deleted successfully from '{selected_primary_subfolder}'.")
                            else:
                                st.info("No files found in the selected Module.")
                    else:
                        st.info(f"No Modules found in '{selected_program_folder}'. Deleting files from the program folder.")

                        # List files in the program folder
                        files = list_files(program_folder_path)
                        if files:
                            selected_file = st.selectbox("Select a file to delete:", files)
                            if st.button("Delete File from Program Folder"):
                                delete_file(program_folder_path, selected_file)
                                st.success(f"File '{selected_file}' deleted successfully from '{selected_program_folder}'.")
                        else:
                            st.info("No files found in the selected program folder.")
            else:
                st.info(f"No program folders found in '{main_folder}'. Add program folders first.")

        elif file_action == "Delete Folders":
            st.subheader("Delete Folders")

            # Select a program folder
            program_folders = list_folders(main_folder)
            if program_folders:
                selected_program_folder = st.selectbox("Select a program folder:", program_folders)
                if selected_program_folder:
                    program_folder_path = os.path.join(main_folder, selected_program_folder)

                    # List Modules
                    primary_subfolders = list_folders(program_folder_path)
                    if primary_subfolders:
                        selected_primary_subfolder = st.selectbox("Select a Module to delete or manage:", primary_subfolders)
                        primary_subfolder_path = os.path.join(program_folder_path, selected_primary_subfolder)

                        # List Topics
                        secondary_subfolders = list_folders(primary_subfolder_path)
                        if secondary_subfolders:
                            selected_secondary_subfolder = st.selectbox("Select a Topic to delete:", secondary_subfolders)
                            secondary_subfolder_path = os.path.join(primary_subfolder_path, selected_secondary_subfolder)

                            # Delete the selected Topic
                            if st.button("Delete Topic"):
                                delete_folder(secondary_subfolder_path)
                                st.success(f"Topic '{selected_secondary_subfolder}' deleted successfully.")
                        else:
                            st.info(f"No Topics found in '{selected_primary_subfolder}'.")

                        # Delete the selected Module
                        if st.button("Delete Module"):
                            delete_folder(primary_subfolder_path)
                            st.success(f"Module '{selected_primary_subfolder}' deleted successfully.")
                    else:
                        st.info(f"No Modules found in '{selected_program_folder}'.")
            else:
                st.info(f"No program folders found in '{main_folder}'. Add program folders first.")
                
    elif admin_option == "Manage Users":
        user_action = st.sidebar.selectbox("User Management Options:", ["View Users", "Edit User", "Delete User"])
        if user_action == "View Users":
            st.subheader("All Registered Users")

            # Filter users by status
            user_status_filter = st.selectbox(
                "Filter Users by Status:",
                ["All Users", "Active Users", "Inactive Users"]
            )

            # Determine status filter value
            if user_status_filter == "Active Users":
                status_filter_value = 1
            elif user_status_filter == "Inactive Users":
                status_filter_value = 0
            else:
                status_filter_value = None  # No filter applied for "All Users"

            # Fetch filtered users
            users_df = fetch_all_users(status_filter_value)

            if not users_df.empty:
                st.dataframe(users_df)  # Display in tabular form
            else:
                st.info(f"No {user_status_filter.lower()} found in the database.")

        elif user_action == "Edit User":
            st.subheader("Edit User")

            # Select Active or Inactive users
            user_status_filter = st.selectbox(
                "Filter Users by Status:",
                ["Active Users", "Inactive Users"]
            )
            status_filter_value = 1 if user_status_filter == "Active Users" else 0

            # Fetch users based on the selected status
             conn = get_db_connection()
            query = "SELECT U_ID, Name FROM User WHERE Status = ?"
            users_df = pd.read_sql_query(query, conn, params=(status_filter_value,))
            conn.close()

            if not users_df.empty:
                user_options = users_df.set_index("U_ID")["Name"].to_dict()
                selected_user_id = st.selectbox(
                    "Select a user to edit:",
                    options=list(user_options.keys()),
                    format_func=lambda x: f"{x} - {user_options[x]}"
                )

                # Fetch details of the selected user
                 conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT Name, Email_ID, Password, Course, Status FROM User WHERE U_ID = ?", (selected_user_id,))
                user_data = cursor.fetchone()
                conn.close()

                if user_data:
                    # Dynamically list courses from subfolders
                    courses = list_folders(MAIN_FOLDER)
                    if courses:
                        # Populate with the current course as default
                        selected_course = st.selectbox(
                            "Select a Course",
                            options=courses,
                            index=courses.index(user_data[3]) if user_data[3] in courses else 0
                        )
                    else:
                        st.error("No courses found.")
                        selected_course = None

                    # Pre-fill the form fields with existing user data
                    name = st.text_input("Name", value=user_data[0])
                    email = st.text_input("Email", value=user_data[1])
                    password = st.text_input("Password", value=user_data[2], type="password")
                    status1 = st.selectbox(
                        "Status",
                        options=["Active", "Inactive"],
                        index=0 if user_data[4] == 1 else 1
                    )
                    # Map status label to corresponding value
                    status_value = 1 if status1 == "Active" else 0

                    # Button to update the profile
                    if st.button("Update Profile"):
                        if name.strip() and email.strip() and password.strip() and selected_course:
                            # Update user in the database
                            edit_user(selected_user_id, name.strip(), email.strip(), password.strip(), selected_course, status_value)
                        else:
                            st.warning("All fields are required.")
                else:
                    st.error("Error fetching user details. Please try again.")
            else:
                st.info(f"No {user_status_filter.lower()} found in the database.")
    
        elif user_action == "Delete User":
                st.subheader("Delete User")
                
                # Fetch all users as a DataFrame
                users_df = fetch_all_users()
                if not users_df.empty:
                    user_options = users_df.set_index("U_ID")["Name"].to_dict()
                    selected_user_id = st.selectbox(
                        "Select a user to delete:",
                        options=list(user_options.keys()),
                        format_func=lambda x: f"{x} - {user_options[x]}"
                    )

                    if st.button("Delete User"):
                        confirm = st.confirmation("Are you sure you want to delete this user?")
                        if confirm:
                            delete_user(selected_user_id)
                        else:
                            st.warning("No user was deleted.")
                else:
                    st.info("No users found in the database.")
    
    elif admin_option == "Manage Courses":
        course_action = st.sidebar.selectbox("Course Management Options:", ["Add New Course", "View Courses", "Edit Courses", "Delete Courses" ])
        if course_action == "Add New Course":
            st.subheader("Add New Course")
            
            # Input fields for the course name and file extension
            new_course_name = st.text_input("Enter the name of the new course:")
            file_extension = st.text_input("Enter the file extension for this course (e.g., '.py', '.txt'):")

            if st.button("Create Course"):
                if new_course_name.strip() and file_extension.strip():
                    # Ensure the file extension starts with a dot
                    if not file_extension.startswith("."):
                        file_extension = f".{file_extension}"

                    course_path = os.path.join(main_folder, new_course_name.strip())
                    try:
                        if not os.path.exists(course_path):
                            # Create the course folder
                            os.makedirs(course_path)

                            # Save the file extension to a metadata file or database
                            metadata_path = os.path.join(course_path, "metadata.txt")
                            with open(metadata_path, "w") as meta_file:
                                meta_file.write(f"File Extension: {file_extension}\n")

                            st.success(f"Course '{new_course_name}' has been added successfully with file extension '{file_extension}'.")
                        else:
                            st.warning(f"Course '{new_course_name}' already exists.")
                    except Exception as e:
                        st.error(f"Error creating course: {e}")
                else:
                    st.warning("Please enter both the course name and file extension.") 

        elif course_action == "View Courses":
            st.subheader("View Courses")

            # List all courses
            courses = list_folders(main_folder)
            if courses:
                st.write("Courses Available:")
                for course in courses:
                    metadata_path = os.path.join(main_folder, course, "metadata.txt")
                    if os.path.exists(metadata_path):
                        with open(metadata_path, "r") as meta_file:
                            file_extension = meta_file.readline().strip().replace("File Extension: ", "")
                        st.write(f"- **{course}** (File Extension: {file_extension})")
                    else:
                        st.write(f"- **{course}** (No metadata found)")
            else:
                st.info("No courses available. Please add a new course.")

        elif course_action == "Edit Courses":
            st.subheader("Edit Course")

            # Select a course to edit
            courses = list_folders(main_folder)
            if courses:
                selected_course = st.selectbox("Select a course to edit:", courses)

                if selected_course:
                    metadata_path = os.path.join(main_folder, selected_course, "metadata.txt")
                    if os.path.exists(metadata_path):
                        with open(metadata_path, "r") as meta_file:
                            file_extension = meta_file.readline().strip().replace("File Extension: ", "")
                    else:
                        file_extension = ""

                    # Input fields to edit course name and file extension
                    new_course_name = st.text_input("Edit Course Name:", value=selected_course)
                    new_file_extension = st.text_input("Edit File Extension:", value=file_extension)

                    if st.button("Update Course"):
                        if new_course_name.strip() and new_file_extension.strip():
                            # Ensure the file extension starts with a dot
                            if not new_file_extension.startswith("."):
                                new_file_extension = f".{new_file_extension}"

                            # Rename course folder
                            new_course_path = os.path.join(main_folder, new_course_name.strip())
                            try:
                                if selected_course != new_course_name.strip():
                                    os.rename(os.path.join(main_folder, selected_course), new_course_path)

                                # Update metadata
                                metadata_path = os.path.join(new_course_path, "metadata.txt")
                                with open(metadata_path, "w") as meta_file:
                                    meta_file.write(f"File Extension: {new_file_extension}\n")

                                st.success(f"Course '{selected_course}' updated successfully!")
                            except Exception as e:
                                st.error(f"Error updating course: {e}")
                        else:
                            st.warning("Please enter valid values for course name and file extension.")
            else:
                st.info("No courses available to edit.")

        elif course_action == "Delete Courses":
            st.subheader("Delete Course")

            # Select a course to delete
            courses = list_folders(main_folder)
            if courses:
                selected_course = st.selectbox("Select a course to delete:", courses)

                if selected_course:
                    if st.button("Confirm Delete"):
                        try:
                            # Delete the course folder and its contents
                            course_path = os.path.join(main_folder, selected_course)
                            for root, dirs, files in os.walk(course_path, topdown=False):
                                for file in files:
                                    os.remove(os.path.join(root, file))
                                for dir in dirs:
                                    os.rmdir(os.path.join(root, dir))
                            os.rmdir(course_path)

                            st.success(f"Course '{selected_course}' has been deleted successfully!")
                        except Exception as e:
                            st.error(f"Error deleting course: {e}")
            else:
                st.info("No courses available to delete.")
        

def list_files(folder_path):
    """List all files in the specified folder."""
    try:
        return [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    except FileNotFoundError:
        return []

def delete_folder(folder_path):
    """Delete a folder and its contents."""
    try:
        for root, dirs, files in os.walk(folder_path, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(folder_path)
        st.success(f"Folder '{folder_path}' and its contents deleted successfully.")
    except FileNotFoundError:
        st.error(f"Folder '{folder_path}' not found.")
    except Exception as e:
        st.error(f"Error deleting folder '{folder_path}': {e}")
          
# Helper Function for Deleting Files
def delete_file(folder_path, file_name):
    """Deletes a file from the specified folder."""
    file_path = os.path.join(folder_path, file_name)
    try:
        os.remove(file_path)
        st.success(f"File '{file_name}' has been deleted successfully.")
    except FileNotFoundError:
        st.error(f"File '{file_name}' not found.")
    except Exception as e:
        st.error(f"Error deleting file: {e}")

# Utility Functions (unchanged from previous)
def list_folders(main_folder):
    """List all subfolders in the specified main folder."""
    try:
        return [folder for folder in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder, folder))]
    except FileNotFoundError:
        st.error(f"The folder '{main_folder}' does not exist.")
        return []

def save_file_to_folder(file, folder_path):
    """Save the uploaded file to the specified folder."""
    os.makedirs(folder_path, exist_ok=True)
    try:
        if isinstance(file, list):  # Check if file is a list (in case of multiple uploads)
            for single_file in file:
                with open(os.path.join(folder_path, single_file.name), "wb") as f:
                    f.write(single_file.getbuffer())
                st.success(f"File '{single_file.name}' saved to folder '{folder_path}'.")
        else:  # If a single file
            with open(os.path.join(folder_path, file.name), "wb") as f:
                f.write(file.getbuffer())
            st.success(f"File '{file.name}' saved to folder '{folder_path}'.")
    except Exception as e:
        st.error(f"Error saving file: {e}")

def create_subfolder(parent_folder, subfolder_name):
    """Create a new subfolder inside an existing subfolder."""
    folder_path = os.path.join(parent_folder, subfolder_name)
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        else:
            st.warning(f"Subfolder '{subfolder_name}' already exists in '{parent_folder}'.")
    except Exception as e:
        st.error(f"Error creating subfolder: {e}")

def edit_user(user_id, name, email, password, course, status1):
     conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE User
            SET Name = ?, Email_ID = ?, Password = ?, Course = ?, status=?
            WHERE U_ID = ?
        """, (name, email, password, course, status1, user_id))
        conn.commit()
        st.success("User updated successfully!")
    except sqlite3.IntegrityError:
        st.error("Email already exists. Please try a different email.")
    conn.close()

# Delete a user
def delete_user(user_id):
     conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM User WHERE U_ID = ?", (user_id,))
    conn.commit()
    conn.close()
    st.success("User deleted successfully!")

# Update user password
def updatepassword(email, new_password):
     conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE User SET Password = ? WHERE Email_ID = ?", (new_password, email))
    conn.commit()
    conn.close()


def user_page():
    """Main User Page containing navigation to Profile, File Browsing, and Change Password."""
    
    if st.sidebar.button("Logout"):
        st.session_state.user = None  # Clear user session  
        st.success("You have been logged out successfully!")
        st.rerun()

    def profile_page():
        """Display the user's profile page."""
        if "user" not in st.session_state or not st.session_state.user:
            #st.error("User session expired. Please log in again.")
            st.stop()

        user = st.session_state.user

        # Display user details
        st.subheader("Your Profile")
        st.write(f"**Name:** {user['name']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Password:** {user['password']}")
        st.write(f"**Course Enrolled:** {user['course']}")

    def change_password_page():
        """Allows the user to change their password."""
        if "user" not in st.session_state or not st.session_state.user:
            st.error("User session expired. Please log in again.")
            st.stop()

        user = st.session_state.user

        st.subheader("Change Your Password")

        # Input fields for password change
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        reenter_new_password = st.text_input("Re-enter New Password", type="password")

        # Validate and process the password change
        if st.button("Change Password"):
            if current_password != user["password"]:
                st.error("The current password is incorrect.")
            elif new_password != reenter_new_password:
                st.error("New passwords do not match. Please try again.")
            elif len(new_password) < 3:
                st.error("Password should be at least 3 characters long.")
            else:
                # Update password in the database
                updatepassword(email=user["email"], new_password=new_password)

                # Update session state with new password
                st.session_state.user["password"] = new_password

                st.success("Password changed successfully!")

    def file_browsing_page():
        """Allows users to browse and view course files."""

        main_folder = MAIN_FOLDER
        user = st.session_state.get("user", {})  # Safely get the user dictionary
        user_course = user.get("course", "Unknown")
        folder_path = os.path.join(main_folder, user_course)
        modules = list_folders(folder_path)

        if modules:
            selected_module = st.sidebar.selectbox("Select a Module:", modules, key="module_select")
            full_module_path = os.path.join(folder_path, selected_module)
            formatted_module_name = selected_module.replace("_", " ").replace("-", " ")  # Replace underscores and hyphens with spaces
            st.title(f"Module: {formatted_module_name}")

            # List topics within the module
            topics = list_folders(full_module_path)
            if topics:
                selected_topic = st.sidebar.selectbox("Select a Topic:", topics, key="topic_select")
                full_topic_path = os.path.join(full_module_path, selected_topic)
                
                files = list_files(full_topic_path)
                if files:
                    display_files_with_pagination(files, full_topic_path, selected_topic)
                else:
                    st.info(f"No files found in the topic `{selected_topic}`.")
            else:
                # No topics, read files directly from the module
                files = list_files(full_module_path)
                if files:
                    display_files_with_pagination(files, full_module_path, selected_module)
                else:
                    st.info(f"No files found in the module `{selected_module}`.")
        else:
            st.info(f"No modules found in `{folder_path}`.")

    def display_files_with_pagination(files, folder_path, folder_name):
        """Helper function to display files with pagination."""
        if "current_file_index" not in st.session_state:
            st.session_state.current_file_index = 0

        file_index = st.session_state.current_file_index
        selected_file = files[file_index]
        file_path = os.path.join(folder_path, selected_file)

        try:
            lines = read_file(file_path)
            if lines:
                lines_per_page = st.sidebar.slider("Lines per page", 5, 20, 10, key="lines_per_page_slider")
                total_pages = (len(lines) - 1) // lines_per_page + 1
                page = st.number_input("Page", min_value=0, max_value=total_pages - 1, value=0, step=1, key="page_number_input")
                st.write(f"Displaying file: **{selected_file}** from `{folder_name}`")
                display_code_page(lines, page, lines_per_page)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Previous Slide", key=f"prev_slide_{file_index}"):  # Unique key for previous button
                        st.session_state.current_file_index = (file_index - 1) % len(files)
                        st.rerun()
                with col2:
                    if st.button("Next Slide", key=f"next_slide_{file_index}"):  # Unique key for next button
                        st.session_state.current_file_index = (file_index + 1) % len(files)
                        st.rerun()

                st.caption(f"Slide {file_index + 1} of {len(files)}")
            else:
                st.warning(f"The file `{selected_file}` appears to be empty.")
        except Exception as e:
            st.error(f"Unable to read the file `{selected_file}`: {e}")

            
    def display_code_page(lines, page, lines_per_page=10):
        """Displays a specific page of code."""
        start_line = page * lines_per_page
        end_line = start_line + lines_per_page
        code_page = lines[start_line:end_line]

        if code_page:
            st.code(''.join(code_page))
        else:
            st.warning("No more lines to display.")
        return len(code_page)

    def list_folders(main_folder):
        """List all subfolders in the specified main folder."""
        try:
            return [folder for folder in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder, folder))]
        except FileNotFoundError:
            st.error(f"The folder '{main_folder}' does not exist.")
            return []

    def list_files(folder_path):
        """List all files in the specified folder."""
        try:
            return [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        except FileNotFoundError:
            st.error("Folder not found. Please check the folder path.")
            return []

    def read_file(filepath):
        """Reads the file and returns its content split into lines."""
        try:
            with open(filepath, 'r') as file:
                return file.readlines()
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return []
   
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Go to", ["Profile", "Browse Files", "Change Password"])

    if page == "Profile":
        profile_page()
    elif page == "Browse Files":
        file_browsing_page()
    elif page == "Change Password":
        change_password_page()
    
if __name__ == "__main__":
    init_db()
    if "page" not in st.session_state:
        st.session_state.page = "login"  # Default to login page

    if st.session_state.page == "otp_verification":
        otp_verification_page()  # Show OTP verification page
    else:
        login_page()  # Show login page
