import random
import os

def generate_bingo_card():
    card = {}

    # Define the number ranges for each column
    ranges = {
        'B': range(1, 16),
        'I': range(16, 31),
        'N': range(31, 46),
        'G': range(46, 61),
        'O': range(61, 76),
    }

    # Populate each column with random numbers within its range
    for letter, number_range in ranges.items():
        if letter == 'N':
            # "N" column has a free space in the center (third row)
            card[letter] = random.sample(number_range, 4)
            card[letter].insert(2, "Free")  # Place "Free" in the third row (index 2)
        else:
            card[letter] = random.sample(number_range, 5)
    
    return card

def save_to_txt(cards_output, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        for card in cards_output:
            for line in card:
                file.write(line + "\n")
            file.write("\n")  # Blank line between cards

def generate_and_save_bingo_cards():
    title = "Alvadore Community Chest Bingo Card"

    cards_output = []
    for _ in range(6):  # Generate 6 unique cards
        card = generate_bingo_card()

        # Create a list for the card's text representation
        card_output = []
        card_output.append(title)
        card_output.append("B\tI\tN\tG\tO")
        card_output.append("--------------------------")

        # Format each row of numbers
        for i in range(5):
            row = []
            for letter in "BINGO":
                cell = str(card[letter][i]).ljust(4)  # Ensure consistent spacing
                row.append(cell)
            card_output.append("\t".join(row))

        cards_output.append(card_output)

    # Print to console
    for card_output in cards_output:
        for line in card_output:
            print(line)
        print()  # Blank line between cards

    # Save to text file with an incremented filename to avoid overwriting
    filename_base = "Alvadore_Community_Chest_Bingo_Cards"
    file_number = 1
    txt_filename = f"{filename_base}_{file_number}.txt"

    while os.path.exists(txt_filename):
        file_number += 1
        txt_filename = f"{filename_base}_{file_number}.txt"

    # Save file
    save_to_txt(cards_output, txt_filename)

    print(f"\nBingo cards saved as '{txt_filename}'")

# Generate and print/save 6 unique Bingo cards
generate_and_save_bingo_cards()
