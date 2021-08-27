new Vue ({
    el: '#filter-app',
    data: {
        novells : []
    },
    created: function (){
        const vm = this;
        axios.get('/api/nov_list/')
            .then(function (response){
                vm.novells =response.data
            })
    }
})