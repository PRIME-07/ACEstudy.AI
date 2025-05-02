from auth import Auth

def main():
    print("Welcome to ACE.ai!")
    print("Press '1' to create an account or '2' to sign in to your account.")

    auth_instance = Auth()

    while True:
        choice = input("Enter your choice: ")

        if choice == '1':
            print("Creating an account...")
            user = auth_instance.sign_up()
            break

        elif choice == '2':
            print("Signing in...")
            user = auth_instance.sign_in()
            break

        else:
            print("Invalid choice. Please enter '1' or '2'.")

if __name__ == "__main__":
    main()
