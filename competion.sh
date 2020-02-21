_record(){
    local commands="start
end
print"
    local tasks="meeting
coding
interview
report
analysis
moving
review
trip"

    local cur=${COMP_WORDS[COMP_CWORD]}
    local prev=${COMP_WORDS[COMP_CWORD-1]}

    if [ $COMP_CWORD -eq 1 ]; then
        local cand="${commands[@]}"
    elif [ $COMP_CWORD -eq 2 ]; then
        local cand=$(echo "select distinct case_ from records" | sqlite3 ~/.record/db.sqlite)
    elif [ $COMP_CWORD -eq 3 ]; then
        local cand="${tasks[@]}"
    elif [ $COMP_CWORD -eq 4 ]; then
        local cand=$(echo "select distinct contents from records" | sqlite3 ~/.record/db.sqlite)
    else
        local cand=""
    fi
    
    COMPREPLY=($(compgen -W "${cand[@]}" -- "${cur}"))
}

complete -F _record record
