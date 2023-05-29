import json

from channels.generic.websocket import WebsocketConsumer

from .models import Question, Choice, Dashboard, UserChoice
from django.utils import timezone
from django.shortcuts import get_object_or_404

from django.core.serializers import serialize

from asgiref.sync import async_to_sync




class PollsConsumer(WebsocketConsumer):

    def connect(self):

        self.dashboard_id = self.scope["url_route"]["kwargs"]["id"]
        self.dashboard_group_name = "dashboard_%s" % self.dashboard_id

        # Join room group
        async_to_sync(self.channel_layer.group_add)(self.dashboard_group_name, self.channel_name)

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(self.dashboard_group_name, self.channel_name)

    # Receive message from WebSocket
    def receive(self, text_data):
        data_json = json.loads(text_data)
        action = data_json["action"]

        if action == "add":
            dashboard_id = data_json["dashboard_id"]
            q_text = data_json["question"]
            dashboard = get_object_or_404(Dashboard, pk=dashboard_id)
            q = Question(dashboard=dashboard, question_text=q_text, pub_date=timezone.now())
            q.save()
            q.choice_set.create(choice_text="Так")
            q.choice_set.create(choice_text="Ні")

            choices = q.choice_set.all()
            choices_id = []
            for choice in choices:
                choices_id.append(choice.id)

            first_q = 0
            if len(Question.objects.filter(dashboard=dashboard)) > 1:
                first_q = 1

            percentages = []
            labelsTemp = []
            labels = []
            for choice in choices:
                labelsTemp.append(choice.choice_text)
                percentages.append(0)
            for i in range(len(labelsTemp)):
                new_item = labelsTemp[i] + " - " + str(percentages[i]) + "%"
                labels.append(new_item)

            async_to_sync(self.channel_layer.group_send)(
                self.dashboard_group_name, {"type": "add_question",
                                       'question_id': q.id,
                                       'question': json.loads(serialize('json', [q]))[0],
                                       'choice1_id': choices_id[0],
                                       'choice2_id': choices_id[1],
                                       'first_q': first_q,
                                       'question_text': q.question_text,
                                       'labels': labels,
                                       'percentages': percentages}
            )

        elif action == "delete_dashboard":
            d = Dashboard.objects.get(pk=data_json["dashboard_id"])
            d.delete()

            async_to_sync(self.channel_layer.group_send)(
                self.dashboard_group_name, {"type": "delete_dashboard"}
            )

        elif action == "clear_votes":
            d = Dashboard.objects.get(pk=data_json["dashboard_id"])
            questions = Question.objects.filter(dashboard=d)

            for question in questions:
                choices = question.choice_set.all()
                for choice in choices:
                    choice.votes_yes = 0
                    choice.save()

                users = question.userchoice_set.all()
                for user in users:
                    user.delete()

            async_to_sync(self.channel_layer.group_send)(
                self.dashboard_group_name, {"type": "clear_votes"}
            )


        elif action == "vote":

            question = Question.objects.get(pk=data_json["question_id"])
            selected_choice = question.choice_set.get(pk=data_json["choice_id"])

            # Check if user has already voted for this question
            ip = data_json["user_ip"]
            user_choices = UserChoice.objects.filter(user_ip=ip, question=question)
            if user_choices.exists():

                user_choice = user_choices.first()

                choice_text = selected_choice.choice_text
                user_choices_text = user_choice.choice
                if choice_text == user_choices_text:
                    # User has already selected this choice, do nothing
                    pass
                else:
                    # User has selected a different choice, update the vote count

                    user_choice.choice = choice_text
                    user_choice.save()

                    selected_choice.votes_yes += 1
                    all_choices = question.choice_set.all()
                    for choice in all_choices:
                        if selected_choice.choice_text != choice.choice_text:
                            choice.votes_yes -= 1
                            choice.save()
                            selected_choice.save()
                            break

            else:
                # User has not voted for this question yet, update the vote count

                #selected_choice.user_ip = ip
                choice_text = selected_choice.choice_text
                new_user = UserChoice(question=question, user_ip=ip, choice=choice_text)
                new_user.save()

                selected_choice.votes_yes += 1
                selected_choice.save()



            choices = question.choice_set.all()
            choices_values = []
            for choice in choices:
                choices_values.append(choice.votes_yes)


            #
            data = []
            labelsTemp = []
            labels = []
            for choice in choices:
                data.append(choice.votes_yes)
                labelsTemp.append(choice.choice_text)
            total_votes = sum(data)
            percentages = [round((d / total_votes) * 100) for d in data]

            for i in range(len(labelsTemp)):
                new_item = labelsTemp[i] + " - " + str(percentages[i]) + "%"
                labels.append(new_item)
            #


            async_to_sync(self.channel_layer.group_send)(
                self.dashboard_group_name, {"type": "vote",
                                            "question_id": data_json["question_id"],
                                            "yes": choices_values[0],
                                            "no": choices_values[1],
                                            "chart_data": percentages,
                                            "labels": labels,
                                            "total_votes": total_votes,
                                            "question_text": question.question_text}
            )

        else:
            dashboard_id = data_json["dashboard_id"]
            dashboard = get_object_or_404(Dashboard, pk=dashboard_id)
            last_q = 0
            if len(Question.objects.filter(dashboard=dashboard)) > 1:
                last_q = 1

            question_id = data_json["question_id"]
            question = Question.objects.get(pk=question_id)
            question.delete()

            async_to_sync(self.channel_layer.group_send)(
                self.dashboard_group_name, {"type": "delete_question",
                                            "question_id": data_json["question_id"],
                                            "last_q": last_q}
            )

    def add_question(self, event):
        question_data = {'action': "add",
                         'question_id': event["question_id"],
                         'question': event["question"],
                         'choice1_id': event["choice1_id"],
                         'choice2_id': event["choice2_id"],
                         'first_q': event["first_q"],
                         'question_text': event["question_text"],
                         'labels': event["labels"],
                         'percentages': event["percentages"]
                         }
        self.send(text_data=json.dumps(question_data))

    def delete_question(self, event):
        self.send(text_data=json.dumps({'action': "delete",
                                        'question_id': event["question_id"],
                                        'last_q': event["last_q"]}))

    def delete_dashboard(self, event):
        self.send(text_data=json.dumps({'action': "delete_dashboard"}))
        self.close()

    def vote(self, event):
        self.send(text_data=json.dumps({'action': "vote",
                                        'question_id': event["question_id"],
                                        'yes': event["yes"],
                                        'no': event["no"],
                                        'chart_data': event["chart_data"],
                                        'labels': event["labels"],
                                        'total_votes': event["total_votes"],
                                        'question_text': event["question_text"]}))

    def clear_votes(self, event):
        self.send(text_data=json.dumps({'action': "clear_votes"}))



