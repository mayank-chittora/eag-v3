package com.newsanalyser.repository;

import com.newsanalyser.model.Category;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.Set;

@Repository
public interface CategoryRepository extends JpaRepository<Category, Long> {
    Optional<Category> findBySlug(String slug);
    Optional<Category> findByName(String name);
    List<Category> findBySlugIn(Set<String> slugs);
    List<Category> findAllByOrderByNameAsc();
}
