"""Story-generation prompt construction."""
from __future__ import annotations


def build_story_prompt(image_descriptions, genre: str, desc_is_array: bool) -> str:
    genre_definition = ""
    if genre == "Comedy":
        genre_definition = "The world is just and strict but finally becomes more free and desirable. The protagonist is initially hilariously vain, self-important and aspiring, but at the end conforms to the world's norms."
    elif genre == "Romance":
        genre_definition = "The world is just but momentarily disturbed by the occurrence of a villainy. The protagonist performs a heroic adventurous quest."
    elif genre == "Tragedy":
        genre_definition = "The world is just but governed by fate and unforgiving. The protagonist misbehaves and finally succumbs and dies."
    elif genre == "Satire":
        genre_definition = "The world is not just, it is dystopian, grotesque and absurd. The protagonist is helpless."
    elif genre == "Mystery":
        genre_definition = "The world is just but has unknown or unexplained or fantastic elements. The protagonist makes a discovery."
    elif genre == "Achiever":
        genre_definition = "An Achiever player focuses on completing challenges, gaining rewards, and demonstrating mastery. Therefore, the narrative must be structured around goal-oriented tasks, measurable progress, milestones, and the desire for recognition. The protagonist is driven by accomplishment and overcoming increasingly difficult challenges."
    elif genre == "Explorer":
        genre_definition = "An Explorer player is focused on discovery, curiosity, and unraveling hidden secrets. Therefore, the narrative must be structured around uncovering mysteries, exploring unknown locations, and the joy of finding something new. The protagonist is driven by a sense of wonder, investigation, and the thrill of the unknown."
    elif genre == "Socializer":
        genre_definition = "A Socializer player focuses on relationships, interactions, and communication. Therefore, the narrative must be structured around friendships, alliances, community building, and the social dynamics between characters. The protagonist is driven by the need for connection, cooperative tasks, and shared experiences."
    elif genre == "Killer":
        genre_definition = "A Killer player focuses on competition, dominance, and asserting power over others. Therefore, the narrative must be structured around conflict, strategic moves, and competitive challenges. The protagonist is driven by a desire for victory, control, and exerting influence over other characters."

    if genre == "Data Storytelling":
        prompt = "Using the following set of sequentially ordered image descriptions, write a compelling narrative that highlights key insights, connects the dots between different data points, and presents a clear and engaging story. The story must have a creative title written using markdown header level 1 (#). Follow the sequence of events as represented in the descriptions, maintaining consistency in mood and context. Ensure the narrative has a clear beginning, middle, and end. Use metaphors, analogies, and emotional appeal to make the story engaging. Avoid referring directly to the images or describing them. Instead, weave the data into the narrative naturally, as if explaining the insights to someone who has never seen the images. Also suggest potential implications, actions, or reflections based on the insights presented. Divide the story into a natural number of chapters, each with a name and number, using markdown header level 2 (##) for the chapter titles. Write your response in english only. \n Image descriptions: \n"
    elif genre == "Achiever" or genre == "Explorer" or genre == "Socializer" or genre == "Killer":
        prompt = "Using the following set of sequentially ordered image descriptions, write a cohesive, engaging and complete story resembling a book narrative. The story must have a creative title written using markdown header level 1 (#). The story must include the sequence of events represented in the descriptions, maintaining consistency in mood and context. In addition, the protagonist's journey presented in the narrative must be based on Bartle's definition of the " + genre + " player type. " + genre_definition + " Ensure the narrative has a clear beginning, middle, and end. Divide the story into a natural number of chapters, each with a name and number, using markdown header level 2 (##) for the chapter titles. When writing the story, assign names to the subjects, describe their visual attributes (eye color, hair color, hairstyle) and clothes (type, color, style), and develop their characters based on their described actions and appearances. Ensure the story incorporates all key elements from the image descriptions, including the subjects, their interactions, and significant environmental details. Focus on creating a narrative and dialogue that brings the story to life, rather than merely describing the images. Exclude any details specific to the image format, such as speech balloons, text boxes, or floating text. Write your response in english only. \n Image descriptions: \n"
    else:
        if genre_definition == "":
            prompt = "Using the following set of sequentially ordered image descriptions, write a cohesive, engaging and complete story resembling a book narrative. The story must have a creative title written using markdown header level 1 (#). When writing the story, assign names to the subjects, describe their visual attributes (eye color, hair color, hairstyle) and clothes (type, color, style), and develop their characters based on their described actions and appearances. Ensure the story incorporates all key elements from the descriptions, including the subjects, their interactions, and significant environmental details. Follow the sequence of events as represented in the descriptions, maintaining consistency in mood and context. Ensure the narrative has a clear beginning, middle, and end. Divide the story into a natural number of chapters, each with a name and number, using markdown header level 2 (##) for the chapter titles. Focus on creating a narrative and dialogue that brings the story to life, rather than merely describing the images. Exclude any details specific to the image format, such as speech balloons, text boxes, or floating text. Write your response in english only. \n Image descriptions: \n"
        else:
            prompt = "Using the following set of sequentially ordered image descriptions, write a cohesive, engaging and complete story resembling a book narrative in the " + genre + " genre. The story must have a creative title written using markdown header level 1 (#). When writing the story, assign names to the subjects, describe their visual attributes (eye color, hair color, hairstyle) and clothes (type, color, style), and develop their characters based on their described actions and appearances. Ensure the story incorporates all key elements from the descriptions, including the subjects, their interactions, and significant environmental details. Follow the sequence of events as represented in the descriptions, maintaining consistency in mood and context. Ensure the narrative has a clear beginning, middle, and end. Divide the story into a natural number of chapters, each with a name and number, using markdown header level 2 (##) for the chapter titles. Incorporate genre-specific elements such as setting, tone, themes, and character types to clearly reflect the " + genre + " genre. Focus on creating a narrative and dialogue that brings the story to life, rather than merely describing the images. Exclude any details specific to the image format, such as speech balloons, text boxes, or floating text. Write your response in english only. Use the following definition for the " + genre + " genre: " + genre_definition + "\n Image descriptions: \n"
    if desc_is_array:
        for i in range(0, len(image_descriptions)):
            prompt = prompt + str(i) + ". " + image_descriptions[i] + "\n"
    else:
        prompt = prompt + image_descriptions

    return prompt


def system_message(genre: str) -> str:
    if genre == "Data Storytelling":
        return "You are an expert data storyteller."
    return "You are a creative story writer."


def regenerate_instruction(genre: str, chapter_title: str) -> str:
    if genre == "Data Storytelling":
        return "Reformulate \"" + chapter_title + "\". Make significant changes to the description and structure of the chapter, while ensuring it stays consistent with the preceding chapters. Feel free to introduce new elements or perspectives. Ensure that the reformulated chapter leads to different developments in the subsequent chapters. Write the full story. Write your response in english only."
    return "Reformulate \"" + chapter_title + "\". Make significant changes to the events, dialogue, and character interactions within this chapter, while ensuring it stays consistent with the preceding chapters. Feel free to introduce new elements, twists, or perspectives. Ensure that the reformulated chapter leads to different developments in the subsequent chapters. Write the full story. Write your response in english only."
