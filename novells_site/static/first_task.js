db.Account.aggregate([{
    $unwind: {
        path: "$sessions"
    }
}, {
    $unwind: {
        path: '$sessions.actions',
        preserveNullAndEmptyArrays: true
    }
}, {
    $group: {
        _id: {_id: '$_id', number: "$number", type: '$sessions.actions.type'},
        'count':
            {"$sum": 1},
        'last':
            {
                '$max': "$sessions.actions.created_at"
            }
    }
}, {
    $group: {
        _id: "$_id._id",
        number: {$first: '$_id.number'},
        'actions': {
            '$push': {
                'type': '$_id.type',
                'last': '$last',
                'count': '$count',
            }
        }
    }
}, {
    $project: {
        _id: 0
    }
}])