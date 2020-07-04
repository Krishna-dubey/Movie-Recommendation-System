from flask import Flask, render_template,url_for,request
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

movies_df=pd.read_csv("movies.csv",na_values=['?'," ",""])
movies_df.genres.replace(to_replace="[|]",value=" ",inplace=True,regex=True)

ratings_df=pd.read_csv("ratings.csv",na_values=['?'," ",""])

# we will consider only that movies that have been rated by atleast 50 users
#so get the movies and count (number of user rated that movie)
count_df=ratings_df.groupby('movieId')['rating'].count()
count_df=count_df[count_df.values>=50]

# for content based
df_content=movies_df.merge(count_df,on="movieId")
cv=CountVectorizer()
cv_matrix=cv.fit_transform(df_content['genres']) #gives the matrix of n*n with count of words matched
cs=cosine_similarity(cv_matrix) #gives cosine similarity
table_content=pd.DataFrame(index=df_content.movieId,columns=df_content.movieId,data=cs)

# for collaborative based
df_merged=ratings_df.merge(movies_df,on="movieId")
df_collab=df_merged.merge(count_df,on='movieId')
table_collab=pd.pivot_table(df_collab,index='userId',columns='movieId',values='rating_x')

def getRandomMoviesList():
    movies_list=[]
    for j in df_content.title.values:
        movies_list.append(j)
    return movies_list

# Based On genre, using cosine similarity
def getContentResult(title):
    # get movie id for given movie title
    movie_id=movies_df[movies_df.title==title]['movieId'].values[0]

    # for given movie id get list of (movieid,similarity)
    movie_similarity=dict(table_content[movie_id])
    movie_similarity.pop(movie_id)#removing the movie details that is provided as input by user

    # sorting in desc order
    sorted_similarity=sorted(movie_similarity.items(),key=lambda x:x[1],reverse=True)

    # top 10 movie recommended for given title
    i=1
    content_movie_ids=[]
    for j in sorted_similarity:
        content_movie_ids.append(j[0])
        if i>10:
            break
        i+=1
    return content_movie_ids

# Based on ratings, using correlation
def getCollaborativeResult(title):
    # get movie id for given movie title
    movie_id=movies_df[movies_df.title==title]['movieId'].values[0]

    #take corr with obtained movie id
    corr_vals=table_collab.corrwith(table_collab[movie_id])

    # drop nan values and sort in desc order
    corr_vals.dropna(inplace=True)
    corr_vals.sort_values(ascending=False,inplace=True)

    # top 10 movie recommended for given title
    i=0
    collab_movie_ids=[]
    for j in corr_vals.index.values:
        if i>10:
            break
        if j!=movie_id:
            collab_movie_ids.append(j)
        i+=1
    return collab_movie_ids

def getFinalRecommendation(result_content,result_collab):
    # check for intersection of 2 results first
    final_recom=set(result_collab).intersection(set(result_content))
    result=[]
    if(len(final_recom)!=0):
        i=1
        for j in final_recom:
            if i>5:
                break
            result.append(movies_df[movies_df.movieId==j]["title"].values[0])
            print(movies_df[movies_df.movieId==j]["title"].values[0])
            i+=1
    else:
        i=1
        # prefer collab result more over content based because dataset was not appropriate for content based
        if len(result_collab)!=0:
            for j in result_collab:
                if i>5:
                    break
                result.append(movies_df[movies_df.movieId==j]["title"].values[0])
                print(movies_df[movies_df.movieId==j]["title"].values[0])
                i+=1
        else:
        # if collab result is empty, then give content result only
            for j in result_collab:
                if i>5:
                    break
                result.append(movies_df[movies_df.movieId==j]["title"].values[0])
                print(movies_df[movies_df.movieId==j]["title"].values[0])
                i+=1

    return result

app=Flask(__name__)

titles=[]

@app.route('/')
def homepage():
    return render_template("index.html",movies=getRandomMoviesList())

@app.route('/watch',methods=['GET','POST'])
def watch():
    if request.method == "POST" or request.method == "GET":
        title=request.form['title']
        titles.append(title)
        return "done"

@app.route('/recommend',methods=['GET','POST'])
def recommend():
    if request.method == "POST" or request.method == "GET":
        if len(titles)==0:
            return render_template("/recommend.html",message="No recommendation, please watch a movie first")
        else:
            content_result=getContentResult(titles[len(titles)-1])
            collab_result=getCollaborativeResult(titles[len(titles)-1])
            recommended_movies=getFinalRecommendation(content_result,collab_result)
            if len(recommended_movies)==0:
                return render_template("/recommend.html",message="No recommendation, please try watching some other movie")
            return render_template("/recommend.html",movies=recommended_movies)

@app.route('/about',methods=['GET','POST'])
def about():
    if request.method == "POST" or request.method == "GET":
        return render_template("/about.html")


if __name__ == '__main__':
    app.run(debug=True)
