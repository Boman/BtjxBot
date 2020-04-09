import os
import json
import traceback

from btjx import decimalencoder, getPartieState
import boto3

dynamodb = boto3.resource('dynamodb')


def getParties(chatID, userID):
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    result = table.get_item(
        Key={
            'idType': "partiesByUser",
            'id': "{}:{}".format(chatID, userID)
        }
    )

    try:
        return "\n".join([getPartieState.getPartieState(partie, ["{}:{}".format(chatID, userID)]) for partie in
                         sorted(result['Item']['partieIDs'])])
    except Exception as ex:
        return ''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__))
    # return "No parties found for you :("
